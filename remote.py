#!/usr/bin/env python3
import atexit
from common import *
from multiprocessing import Process
import os
import queue

_listening_sockets = []


@atexit.register
def close_listening_socket_at_exit():
    log.info("exiting...")
    for s in _listening_sockets:
        log.info("closing: {}".format(s))
        try_close(s)


def try_bind_port(sock, addr):
    while True:
        try:
            sock.bind(addr)
        except Exception as e:
            log.error(("unable to bind {}, {}. If this port was used by the recently-closed shootback itself\n"
                       "then don't worry, it would be available in several seconds\n"
                       "we'll keep trying....").format(addr, e))
            log.debug(traceback.format_exc())
            time.sleep(3)
        else:
            break


class Remote(object):

    def __init__(self, customer_listen_addr, communicate_addr=None,
                 local_pool=None, working_pool=None):
        self.thread_pool = {}
        self.thread_pool["spare_local"] = {}
        self.thread_pool["working_local"] = {}

        self.working_pool = working_pool or {}

        self.socket_bridge = SocketBridge()

        self.pending_customers = queue.Queue()

        self.communicate_addr = communicate_addr

        _fmt_communicate_addr = fmt_addr(self.communicate_addr)

        if local_pool:
            self.external_local = True
            self.thread_pool["listen_local"] = None
        else:
            self.external_local = False
            self.local_pool = collections.deque()
            self.thread_pool["listen_local"] = threading.Thread(
                target=self._listen_local,
                name="listen_local-{}".format(_fmt_communicate_addr),
                daemon=True,
            )

        self.customer_listen_addr = customer_listen_addr
        self.thread_pool["listen_customer"] = threading.Thread(
            target=self._listen_customer,
            name="listen_customer-{}".format(_fmt_communicate_addr),
            daemon=True,
        )

        self.thread_pool["heart_beat_daemon"] = threading.Thread(
            target=self._heart_beat_daemon,
            name="heart_beat_daemon-{}".format(_fmt_communicate_addr),
            daemon=True,
        )

        self.thread_pool["assign_local_daemon"] = threading.Thread(
            target=self._assign_local_daemon,
            name="assign_local_daemon-{}".format(_fmt_communicate_addr),
            daemon=True,
        )

    def serve_forever(self):
        if not self.external_local:
            self.thread_pool["listen_local"].start()
        self.thread_pool["heart_beat_daemon"].start()
        self.thread_pool["listen_customer"].start()
        self.thread_pool["assign_local_daemon"].start()
        self.thread_pool["socket_bridge"] = self.socket_bridge.start_as_daemon()

        while True:
            time.sleep(10)

    def _transfer_complete(self, addr_customer):
        log.info("customer complete: {}".format(addr_customer))
        del self.working_pool[addr_customer]

    def _serve_customer(self, conn_customer, conn_local):
        self.socket_bridge.add_conn_pair(
            conn_customer, conn_local,
            functools.partial(
                self._transfer_complete,
                conn_customer.getpeername()
            )
        )

    @staticmethod
    def _send_heartbeat(conn_local):
        conn_local.send(CtrlPkg.pbuild_heart_beat().raw)

        pkg, verify = CtrlPkg.recv(
            conn_local, expect_ptype=CtrlPkg.PTYPE_HEART_BEAT)

        if not verify:
            return False

        if pkg.prgm_ver < 0x000B:
            pass
        else:
            conn_local.send(CtrlPkg.pbuild_heart_beat().raw)

        return verify

    def _heart_beat_daemon(self):

        default_delay = 5 + SPARE_TTL // 12
        delay = default_delay
        log.info("heart beat daemon start, delay: {}s".format(delay))
        while True:
            time.sleep(delay)

            local_count = len(self.local_pool)
            if not local_count:
                log.warning("heart_beat_daemon: sorry, no local available, keep sleeping")
                delay = default_delay
                continue
            else:
                delay = 1 + SPARE_TTL // max(local_count * 2 + 1, 12)

            local = self.local_pool.popleft()
            addr_local = local["addr_local"]

            start_time = time.perf_counter()
            try:
                hb_result = self._send_heartbeat(local["conn_local"])
            except Exception as e:
                log.warning("error during heartbeat to {}: {}".format(
                    fmt_addr(addr_local), e))
                log.debug(traceback.format_exc())
                hb_result = False
            finally:
                time_used = round((time.perf_counter() - start_time) * 1000.0, 2)

            if not hb_result:
                log.warning("heart beat failed: {}, time: {}ms".format(
                    fmt_addr(addr_local), time_used))
                try_close(local["conn_local"])
                del local["conn_local"]

                delay = 0

            else:
                log.debug("heartbeat success: {}, time: {}ms".format(
                    fmt_addr(addr_local), time_used))
                self.local_pool.append(local)

    @staticmethod
    def _handshake(conn_local):
        conn_local.send(CtrlPkg.pbuild_hs_m2s().raw)

        buff = select_recv(conn_local, CtrlPkg.PACKAGE_SIZE, 2)
        if buff is None:
            return False

        pkg, verify = CtrlPkg.decode_verify(buff, CtrlPkg.PTYPE_HS_S2M)

        log.debug("CtrlPkg from local {}: {}".format(conn_local.getpeername(), pkg))

        return verify

    def _get_an_active_local(self):
        try_count = 100
        while True:
            try:
                dict_local = self.local_pool.popleft()
            except Exception:
                if try_count:
                    time.sleep(0.02)
                    try_count -= 1
                    if try_count % 10 == 0:
                        log.error("!!NO SLAVER AVAILABLE!!  trying {}".format(try_count))
                    continue
                return None

            conn_local = dict_local["conn_local"]

            try:
                hs = self._handshake(conn_local)
            except Exception as e:
                log.warning("Handshake failed: {}".format(e))
                log.debug(traceback.format_exc())
                hs = False

            if hs:
                return conn_local
            else:
                log.warning("local handshake failed: {}".format(dict_local["addr_local"]))
                try_close(conn_local)

                time.sleep(0.02)

    def _assign_local_daemon(self):
        while True:
            conn_customer, addr_customer = self.pending_customers.get()

            conn_local = self._get_an_active_local()
            if conn_local is None:
                log.warning("Closing customer[{}] because no available local found".format(
                    addr_customer))
                try_close(conn_customer)

                continue
            else:
                log.debug("Using local: {} for {}".format(conn_local.getpeername(), addr_customer))

            self.working_pool[addr_customer] = {
                "addr_customer": addr_customer,
                "conn_customer": conn_customer,
                "conn_local": conn_local,
            }

            try:
                self._serve_customer(conn_customer, conn_local)
            except Exception:
                try:
                    try_close(conn_customer)
                except Exception:
                    pass
                continue

    def _listen_local(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try_bind_port(sock, self.communicate_addr)
        sock.listen(10)
        _listening_sockets.append(sock)
        log.info("Listening for locals: {}".format(
            fmt_addr(self.communicate_addr)))
        while True:
            conn, addr = sock.accept()
            self.local_pool.append({
                "addr_local": addr,
                "conn_local": conn,
            })
            log.info("Got local {} Total: {}".format(
                fmt_addr(addr), len(self.local_pool)
            ))

    def _listen_customer(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try_bind_port(sock, self.customer_listen_addr)
        sock.listen(20)
        _listening_sockets.append(sock)
        log.info("Listening for customers: {}".format(
            fmt_addr(self.customer_listen_addr)))
        while True:
            conn_customer, addr_customer = sock.accept()
            log.info("Serving customer: {} Total customers: {}".format(
                addr_customer, self.pending_customers.qsize() + 1
            ))

            self.pending_customers.put((conn_customer, addr_customer))


def remote_processing(mid_port, remote_port):
    communicate_addr = split_host('0.0.0.0:%s' % mid_port)
    customer_listen_addr = split_host('0.0.0.0:%s' % remote_port)
    CtrlPkg.recalc_crc32()

    Remote(customer_listen_addr, communicate_addr).serve_forever()


if __name__ == '__main__':
    for ports in PORTS_LIST:
        mid_port = ports.split(':')[1]
        remote_port = ports.split(':')[2]
        killport_path = os.path.join(os.path.dirname(__file__), 'killport')
        os.system('bash %s %s' % (killport_path, mid_port))
        os.system('bash %s %s' % (killport_path, remote_port))
        print('start remote processing (%s)' % ports)
        p = Process(target=remote_processing, args=(mid_port, remote_port,))
        p.start()
