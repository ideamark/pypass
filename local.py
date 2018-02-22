#!/usr/bin/env python3
from __future__ import print_function, unicode_literals, division, absolute_import

from common import *


class Local(object):

    def __init__(self, communicate_addr, target_addr, MAX_SPARE_COUNT=5):
        self.communicate_addr = communicate_addr
        self.target_addr = target_addr
        self.MAX_SPARE_COUNT = MAX_SPARE_COUNT

        self.spare_local_pool = {}
        self.working_pool = {}
        self.socket_bridge = SocketBridge()

    def _connect_remote(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.communicate_addr)

        self.spare_local_pool[sock.getsockname()] = {
            "conn_local": sock,
        }

        return sock

    def _connect_target(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(self.target_addr)

        log.debug("connected to target[{}] at: {}".format(
            sock.getpeername(),
            sock.getsockname(),
        ))

        return sock

    def _response_heartbeat(self, conn_local, hb_from_remote):
        if hb_from_remote.prgm_ver < 0x000B:
            conn_local.send(CtrlPkg.pbuild_heart_beat().raw)
            return True
        else:
            conn_local.send(CtrlPkg.pbuild_heart_beat().raw)
            pkg, verify = CtrlPkg.recv(
                conn_local,
                expect_ptype=CtrlPkg.PTYPE_HEART_BEAT)
            if verify:
                log.debug("heartbeat success {}".format(
                    fmt_addr(conn_local.getsockname())))
                return True
            else:
                log.warning(
                    "received a wrong pkg[{}] during heartbeat, {}".format(
                        pkg, conn_local.getsockname()
                    ))
                return False

    def _stage_ctrlpkg(self, conn_local):
        while True:

            pkg, verify = CtrlPkg.recv(conn_local, SPARE_TTL)

            if not verify:
                return False

            log.debug("CtrlPkg from {}: {}".format(conn_local.getpeername(), pkg))

            if pkg.pkg_type == CtrlPkg.PTYPE_HEART_BEAT:
                if not self._response_heartbeat(conn_local, pkg):
                    return False

            elif pkg.pkg_type == CtrlPkg.PTYPE_HS_M2S:

                break

        conn_local.send(CtrlPkg.pbuild_hs_s2m().raw)

        return True

    def _transfer_complete(self, addr_local):
        del self.working_pool[addr_local]
        log.info("local complete: {}".format(addr_local))

    def _local_working(self, conn_local):
        addr_local = conn_local.getsockname()
        addr_remote = conn_local.getpeername()

        try:
            hs = self._stage_ctrlpkg(conn_local)
        except Exception as e:
            log.warning("local{} waiting handshake failed {}".format(
                fmt_addr(addr_local), e))
            log.debug(traceback.print_exc())
            hs = False
        else:
            if not hs:
                log.warning("bad handshake or timeout between: {} and {}".format(
                    fmt_addr(addr_remote), fmt_addr(addr_local)))

        if not hs:
            del self.spare_local_pool[addr_local]
            try_close(conn_local)

            log.warning("a local[{}] abort due to handshake error or timeout".format(
                fmt_addr(addr_local)))
            return
        else:
            log.info("Success remote handshake from: {} to {}".format(
                fmt_addr(addr_remote), fmt_addr(addr_local)))

        self.working_pool[addr_local] = self.spare_local_pool.pop(addr_local)

        try:
            conn_target = self._connect_target()
        except Exception:
            log.error("unable to connect target")
            try_close(conn_local)

            del self.working_pool[addr_local]
            return
        self.working_pool[addr_local]["conn_target"] = conn_target

        self.socket_bridge.add_conn_pair(
            conn_local, conn_target,
            functools.partial(
                self._transfer_complete, addr_local
            )
        )

        return

    def serve_forever(self):
        self.socket_bridge.start_as_daemon()

        err_delay = 0
        max_err_delay = 15
        spare_delay = 0.08
        default_spare_delay = 0.08

        while True:
            if len(self.spare_local_pool) >= self.MAX_SPARE_COUNT:
                time.sleep(spare_delay)
                spare_delay = (spare_delay + default_spare_delay) / 2.0
                continue
            else:
                spare_delay = 0.0

            try:
                conn_local = self._connect_remote()
            except Exception as e:
                log.warning(e)
                log.debug(traceback.format_exc())
                time.sleep(err_delay)
                if err_delay < max_err_delay:
                    err_delay += 1
                continue

            try:
                t = threading.Thread(target=self._local_working,
                                     args=(conn_local,)
                                     )
                t.daemon = True
                t.start()

                log.info("connected to remote[{}] at {} total: {}".format(
                    fmt_addr(conn_local.getpeername()),
                    fmt_addr(conn_local.getsockname()),
                    len(self.spare_local_pool),
                ))
            except Exception as e:
                log.error("unable create Thread: {}".format(e))
                log.debug(traceback.format_exc())
                time.sleep(err_delay)

                if err_delay < max_err_delay:
                    err_delay += 1
                continue

            err_delay = 0

        time.sleep(3)


def local_processing(mid_port, local_port):
    communicate_addr = split_host('%s:%s' % (REMOTE_IP, mid_port))
    target_addr = split_host('127.0.0.1:%s' % local_port)
    CtrlPkg.recalc_crc32()
    Local(communicate_addr, target_addr, MAX_SPARE_COUNT=MAX_SPARE_COUNT).serve_forever()


if __name__ == '__main__':
    for ports in PORTS_LIST:
        mid_port = ports.split(':')[1]
        local_port = ports.split(':')[0]
        print('start local processing (%s)' % ports)
        p = Process(target=local_processing, args=(mid_port, local_port,))
        p.start()
