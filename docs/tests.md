# Test procedures and results

The virtual runs use 7250 IXR-e3x SR-SIM with SR OS 26.10.R1 and Cisco IOS XRd 26.2.1. The selected [evidence](evidence.txt) contains lab output with device-specific management details and link MAC addresses removed.

| Requirement | Lab outcome |
| --- | --- |
| IS-IS Levels 1 and 2 and SR-MPLS | IXR and XRd formed Level 2 adjacencies in the default setup and a Level 1 adjacency in a separate baseline run. The SR database showed the remote Prefix-SID at Level 1 with the common SRGB 16000–23999. Each router advertised an Adjacency-SID. PE1 popped its local Adjacency-SID and forwarded all three injected probes to P2 with the inner label intact. |
| Single-hop IPv4 BFD for IS-IS | The PE1/P1 IXR pair reached Up in both directions with 300 ms intervals and multiplier 3. With the same configuration toward XRd Control Plane, the Nokia session stayed Down with no received BFD packets. XRd showed IS-IS IPv4 BFD Init. |
| BGP-LU | IXR accepted IPv4 labels 0, 3 and a regular label. It also received a BGP Prefix-SID. The normal label test checked reception. |
| PHP and explicit-null | In L3VPN v4/v6, a capture toward Cisco showed the service label alone with PHP and `0 + service label` with explicit-null. An IPv4 injection test also verified IXR as egress. Nokia documents its own advertised IS-IS Prefix-SIDs with `P=1, E=0`. Nonzero TC propagation through every imposed label remains unverified. |
| TI-LFA link, node and SRLG | Node-protect TI-LFA was programmed for the remote Prefix-SID. Cutting the primary core link moved traffic to the alternate. A separate run isolated all three P1 data links in one commit. The tunnel moved to P2 and 60 out of 60 probes succeeded at 200 ms intervals. A shared SRLG suppressed the repair, which returned after removing the shared-risk tag from the alternate. |
| BGP PIC for BGP-LU | Two labeled paths used distinct next hops. IXR had the backup before withdrawal and used it after the primary peering was disabled. Probes succeeded before and after. The test did not measure switching time. |
| PCEP and colored SR policy | A PCC-initiated color-101 candidate path was delegated and installed after Cisco computed it. Cisco originated an ordinary PCE-initiated SR-TE LSP. The PCE-initiated attempt did not install a colored SR policy. |
| BGP-LS and Flex-Algo | Cisco received eight topology NLRIs on the baseline. On the services topology, Flex-Algo 128 excluded the primary affinity and resolved through p2 with SID 16104. |
| Automated steering by color and ODN | Color 101 resolved to an installed SR policy in the FIB. Color 102 triggered an on-demand SR-TE LSP and used it. Withdrawal removed the route and tunnel. Re-advertisement recreated them. |
| EVPN-VPWS and FAT | Both endpoints brought up EVPN-MPLS VPWS. Captures showed Nokia imposing the FAT label and the labeled Ethernet frame reaching Cisco. Host-to-host forwarding did not pass on the tested XRd image. |
| EVPN-ELAN | EVPN/MPLS destinations came up. Host-to-host Ethernet forwarding did not pass on the tested XRd image. |
| L3VPN IPv4/IPv6 | Host-to-host probes passed for both address families with PHP and explicit-null toward Cisco. |
| Sampled NetFlow v9 and IPFIX | Ingress records in both formats contained all four labels of the injected test stack. Hardware sampling capacity and forwarding impact remain open. |
| Four-label PUSH in one ASIC pass | Hardware validation remains open for transport SID, BGP-LU, service and FAT in the same stack. Nokia documents a Gen 3c push budget of 10 transport labels, a service label and ELI/EL. A sampled four-label input and a virtual egress capture cannot establish ASIC pass count. |

## Services and protection

Apply `configs/pe2-underlay.cli` after deploying [the services topology](../diamond.clab.yml). Confirm both IS-IS adjacencies to PE2. On Nokia, open `configure exclusive`, paste the applicable `.partial.txt` commands, then `commit` and `exit all`. Apply the `.cli` files in PE2's IOS XR CLI. Configure the Linux host VLANs once with `sudo bash configure-hosts.sh`.

### PHP and explicit-null

1. Apply [PE1 VPWS and BGP](../configs/pe1-vpws.partial.txt), [PE2 VPWS and BGP](../configs/pe2-vpws.cli), [PE1 VPNs](../configs/pe1-vpn.partial.txt) and [PE2 VPNs](../configs/pe2-vpn.cli).
2. On the host run `bash tools/check-vpn.sh`. Capture the two PE2 core links with `bash tools/capture-core.sh` or the matching TopoViewer button while sending the probes. Inspect MPLS on the core link to PE2. With the default Cisco Prefix-SID, PHP removes the outer transport label.
3. Apply [Cisco explicit-null](../configs/pe2-explicit-null.cli), wait for IS-IS convergence and repeat the capture. The outer label on PE2 ingress is 0 over the VPN service label. This is an IPv4 transport SID for both VPN payload families.
4. To check IXR as IPv4 egress, inject UDP on the P1-facing link using the current PE1 VPN service label alone, then with label 0 above it. Capture the customer's access VLAN. In the recorded run all three packets in each group reached VLAN 300.
5. Restore Cisco PHP with `prefix-sid index 4` under the IPv4 address family of IS-IS Loopback0.

### EVPN-VPWS and EVPN-ELAN

- Check VPWS signaling with `show service id 100 evpn-mpls` on PE1 and `show l2vpn xconnect detail` on PE2. Test VLAN 100 with `docker exec clab-sr-interop-host1 ping -c 5 203.0.113.2`.
- Apply [Nokia FAT](../configs/pe1-vpws-fat.partial.txt) and [Cisco FAT](../configs/pe2-vpws-fat.cli). On the core toward PE2, a FAT label is bottom-of-stack with TTL 0. Record any distinction between core arrival and access delivery.
- Check ELAN with `show service id 200 evpn-mpls` on PE1 and `show l2vpn bridge-domain brief` on PE2. Test VLAN 200 with `docker exec clab-sr-interop-host1 ping -c 5 203.0.113.66`.
- Repeat end-to-end L2, FAT and QoS tests with a Cisco endpoint supporting the required EVPN-MPLS forwarding. Capture traffic at both access interfaces.

### TI-LFA, SRLG, Flex-Algo and PIC

1. Apply [PE1 protection](../configs/pe1-protection.partial.txt). Observe `show router tunnel-table 192.0.2.4/32 detail` and `tools dump router isis sr-database`. The latter identifies TI-LFA node protection as `Tn`.
2. Start continuous L3VPN traffic. Disable PE1 port `1/1/c1/1`, verify the route moves to `to-p2`, and re-enable the port. For node isolation, disable P1 ports `1/1/c1/1`, `1/1/c2/1` and `1/1/c3/1` in one commit. Check that the regular tunnel metric to `192.0.2.4/32` changes from 20 to 60 and restore all three ports. The 200 ms probe interval is the observation granularity.
3. Apply [the SRLG scenario](../configs/pe1-srlg.partial.txt). With both PE1 branches in SRLG 7, the programmed repair disappears. Delete the `SHARED` SRLG membership from interface `to-p2` and check that the repair is installed again.
4. Apply the Flex-Algo overlays for [pe1](../configs/pe1-flex-algo.partial.txt), [p1](../configs/p1-flex-algo.partial.txt), [p2](../configs/p2-flex-algo.partial.txt) and [pe2](../configs/pe2-flex-algo.cli). Read `show router tunnel-table 192.0.2.4/32 detail`. The normal SID uses p1 and algorithm 128 uses p2. This tests an IS-IS affinity, separately from PCE optimization.
5. Apply PIC overlays for [pe1](../configs/pe1-pic.partial.txt), [p1](../configs/p1-pic.partial.txt) and [p2](../configs/p2-pic.partial.txt). Verify `Backup-Path: Yes` with `show router route-table 203.0.113.241/32 extensive` on PE1. Disable BGP neighbor `192.0.2.2`, verify P2 becomes the active next hop and ping the prefix. Re-enable the neighbor.

### IS-IS Level 1, Adjacency-SID and BFD

- On the two-node baseline, change IXR IS-IS instance 0 to `level-capability 1`. Change XRd to `is-type level-1` and remove `mpls traffic-eng level-2-only` from its IS-IS IPv4 address family for the run. Check `show router isis adjacency` and `tools dump router isis sr-database` on IXR, plus `show isis adjacency` and `show isis database verbose` on XRd. Restore Level 2 and the XRd traffic engineering setting afterward.
- On the services topology, read PE1's current local Adjacency-SID for P2 with `show router isis database detail`. Inject three MPLS packets on P1's link to PE1 with that SID on top and the P2 node SID 16003 at bottom of stack. Set the Ethernet destination to PE1's MAC learned by P1. Capture the PE1-to-P2 link and check that all three packets exit with only label 16003. The dynamically allocated Adjacency-SID in the recorded run was 1048574.
- On both Nokia routers in the services topology, set `transmit-interval 300`, `receive 300`, `multiplier 3` and `admin-state enable` under the link's `ipv4 bfd` context. Set `bfd-liveness ipv4` under the matching IS-IS interface. Use `to-p1` on PE1 and `to-pe1` on P1. Verify both sessions with `show router bfd session`.
- For the Cisco interop check, use `to-xr` on baseline PCC and set `bfd minimum-interval 300`, `bfd multiplier 3` and `bfd fast-detect ipv4` on XRd under IS-IS interface `GigabitEthernet0/0/0/0`. Compare `show router bfd session` and `show bfd session` with the IS-IS adjacency on each router.

## PCEP and telemetry

Deploy [the baseline topology](../baseline.clab.yml) and apply [the IOS XR configuration](../configs/pce.cli). On PCC use `show router pcep pcc peer` and `show router segment-routing sr-policies all`. On PCE use `show pce lsp detail`.

- Confirm locally configured `PCC-COLOR-101` is active and Cisco reports color 101. Compare the separate Cisco `PCInitiate` case with `show router mpls sr-te-lsp auto-lsp all detail` on PCC. The original run showed an ordinary `pceInitP2PSrTe` for the PCE-initiated request. The capture did not establish which association objects Cisco sent in that request. Nokia SR OS documentation lists PCE initiation and control of colored candidate paths as unsupported. [Nokia PCEP Guide](https://documentation.nokia.com/sr/26-10/7x50-shared/segment-routing-pce-user/pcep.html)
- Verify labeled IPv4 routes with `show router bgp routes label-ipv4 detail`. Inspect BGP-LS nodes, links and prefixes on Cisco with `show bgp link-state link-state neighbors 192.0.2.2 routes`.
- Check PCC FIB for `203.0.113.101/32` via SR Policy and `203.0.113.102/32` via the on-demand SR-TE tunnel. Withdraw and re-advertise the latter with IOS XR BGP `no network 203.0.113.102/32` and `network 203.0.113.102/32` under IPv4 unicast. Check tunnel creation and deletion.
- For cflowd, assign the host test address and start the collector. In a second shell, obtain the PCC MAC with ARP and run the MPLS packet sender. Allow time for templates and records to flush.

```sh
sudo ip address replace 198.18.0.0/31 dev pce-lab-collector
sudo ip address replace 203.0.113.114/32 dev pce-lab-collector
sudo ip link set pce-lab-collector up
sudo ip route replace 203.0.113.101/32 via 198.18.0.1 dev pce-lab-collector
mkdir -p test-output
python3 tools/collect-netflow.py > test-output/netflow.log
```

```sh
ping -c 2 198.18.0.1
mac=$(ip neigh show to 198.18.0.1 dev pce-lab-collector | awk '{for (i=1; i<NF; i++) if ($i=="lladdr") print $(i+1)}')
sudo python3 tools/send-mpls.py pce-lab-collector "$mac"
# After the collector exits
python3 tools/decode-netflow.py test-output/netflow.log
```

Both formats should show `direction=0` and `[24501, 7, 12345, 0]` for source port 6004. In this test 24501 was the binding SID, 7 was ELI, 12345 was EL and 0 was IPv4 explicit-null. Labels were injected at ingress for the sampling test.

## Hardware evidence still required

- Verify the exact four-label imposition stack and the repair stack on physical IXR-e3x. A wire capture proves label order and TC values. ASIC diagnostics or platform confirmation is needed to prove a single pass without recirculation.
- Measure sampled cflowd under the intended ingress packet rate and traffic mix. Compare CPU, forwarding throughput, latency and collector gaps at the target rate and with cflowd disabled.
- Optics, timing, capacity and hardware convergence targets require their own physical acceptance runs.

[Nokia SR-MPLS Guide](https://documentation.nokia.com/sr/26-10/7x50-shared/segment-routing-pce-user/segment-rout-with-mpls-data-plane-sr-mpls.html) · [Cisco IOS XRd data sheet](https://www.cisco.com/c/en/us/products/collateral/routers/ios-xrd/ios-xrd-ds.html)
