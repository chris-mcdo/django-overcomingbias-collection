"""Behavior test in an EMPTY network namespace: sudo unshare -n python3 this.py.

Never run in the host namespace. The --isolated flag is only set by check.sh/CI.
"""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isolated", action="store_true", required=True)
    parser.parse_args()
    # Do not create interfaces or rules unless the namespace contains only lo.
    links = json.loads(run("ip", "-j", "link"))
    if [link["ifname"] for link in links] != ["lo"]:
        raise SystemExit("Refusing to test outside an empty network namespace")
    peer = subprocess.Popen(["unshare", "-n", "sleep", "60"])
    sockets = []
    try:
        # Wait until unshare has created the child's network namespace.
        import time
        for attempt in range(100):
            if os.readlink(f"/proc/{peer.pid}/ns/net") != os.readlink("/proc/self/ns/net"):
                break
            time.sleep(0.01)
        else:
            raise RuntimeError("Peer namespace did not start")
        run("ip", "link", "add", "eth0", "type", "veth", "peer", "name", "probe0")
        run("ip", "link", "set", "probe0", "netns", str(peer.pid))
        run("ip", "addr", "add", "192.0.2.1/24", "dev", "eth0")
        run("ip", "-6", "addr", "add", "2001:db8::1/64", "dev", "eth0", "nodad")
        run("ip", "link", "set", "eth0", "up")
        run("nsenter", "-t", str(peer.pid), "-n", "ip", "addr", "add", "192.0.2.2/24", "dev", "probe0")
        run("nsenter", "-t", str(peer.pid), "-n", "ip", "link", "set", "probe0", "up")
        run("nsenter", "-t", str(peer.pid), "-n", "ip", "-6", "addr", "add", "2001:db8::2/64", "dev", "probe0", "nodad")
        rules = Path(__file__).with_name("angara-swarm.nft")
        run("nft", "-f", str(rules))
        # These listeners exist solely in this throwaway namespace.
        for family, address in [(socket.AF_INET, "192.0.2.1"), (socket.AF_INET6, "2001:db8::1")]:
            for port in [22, 80, 443, 2377, 7946]:
                sock = socket.socket(family)
                if family == socket.AF_INET6:
                    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
                sock.bind((address, port))
                sock.listen()
                sockets.append(sock)
        probe = '''import socket
for family,address in [(socket.AF_INET,'192.0.2.1'),(socket.AF_INET6,'2001:db8::1')]:
 for port in [22,80,443,2377,7946]:
  s=socket.socket(family); s.settimeout(0.3)
  result=s.connect_ex((address,port)); s.close()
  assert (result == 0) == (port in [22,80,443]), (address,port,result)
 for port in [4789,7946]:
  s=socket.socket(family,socket.SOCK_DGRAM)
  s.sendto(b'synthetic-probe',(address,port)); s.close()
'''
        run("nsenter", "-t", str(peer.pid), "-n", sys.executable, "-c", probe)
        ruleset = json.loads(run("nft", "-j", "list", "table", "inet", "obcollection_swarm"))
        counters = [expr["counter"]["packets"] for entry in ruleset["nftables"]
                    if "rule" in entry for expr in entry["rule"]["expr"] if "counter" in expr]
        assert len(counters) == 2 and all(value >= 4 for value in counters), counters
        print("PASS: public Swarm TCP/UDP dropped; SSH/HTTP/HTTPS still reachable; IPv4 and IPv6 verified")
    finally:
        for sock in sockets:
            sock.close()
        peer.terminate()
        peer.wait()


if __name__ == "__main__":
    main()
