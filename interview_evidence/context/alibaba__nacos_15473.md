# Issue Context Dossier: `alibaba/nacos` #15473

**Title:** Nacos1.4.2版本集群扩容和缩容问题  
**Repository:** https://github.com/alibaba/nacos  
**Language:** Java  
**Suitability Score:** 92/100 (ContributionComplexity.BEGINNER)  
**Availability Status:** `CHECK_DISCUSSION`  

---

## 1. Problem Summary & Objective
> The user experienced cluster expansion (adding a node) and contraction (removing a node) issues in Nacos 1.4.2 using cluster.conf and Raft metadata. When scaling out or in without resetting persistent data or properly updating node membership across all members, Raft state becomes unstable (showing only raftPort or bouncing/jumping states) and client applications experience 'Load balancer does not have available server for client' errors.

## 2. Root Cause Analysis
> In Nacos 1.4.x, Raft consensus metadata and persistent local data directories (such as the 'data' directory containing Raft logs and state machines) are tightly coupled to node identities defined in cluster.conf. Modifying membership or replacing nodes without clearing local persistent state or following precise Raft quorum expansion/contraction protocols leads to consensus state divergence and unstable metadata propagation.

## 3. Grounded Code Locations & Citations
- *General repository target scope*

## 4. Actionable Step-by-Step Fix Plan
1. **Inspect Raft metadata and cluster.conf handling**: Inspect symbol cluster.conf parsing and Raft metadata initialization logic in the cluster management module to understand how node membership changes are processed. (Target: `naming/src/main/java/com/alibaba/nacos/naming/cluster/raft/RaftPeerSet.java`)
2. **Analyze node addition and removal synchronization**: Examine how node join and leave events update the persistent Raft state machine and prevent stale peer configurations during expansion and contraction. (Target: `naming/src/main/java/com/alibaba/nacos/naming/cluster/raft/RaftCore.java`)
3. **Implement robust membership validation and error recovery**: Refine the membership update validation to handle transient node dropouts gracefully and prevent bouncing/jumping raftPort states across cluster members. (Target: `naming/src/main/java/com/alibaba/nacos/naming/cluster/raft/RaftCore.java`)
4. **Add regression test for cluster expansion and contraction**: Create a regression test verifying that adding and removing nodes via cluster.conf updates correctly without corrupting Raft metadata or causing client service discovery load balancer errors. (Target: `naming/src/test/java/com/alibaba/nacos/naming/cluster/raft/RaftCoreTest.java`)
5. **Run test suite to verify stability**: Run the naming and cluster test suites to confirm that cluster scaling operations maintain stable consensus and pass all verification checks. (Target: `None`)

## 5. Educational Concepts
### Raft Consensus Metadata & Cluster Membership
- **What is it:** Raft is a consensus algorithm used by Nacos to manage replicated logs and maintain consistent cluster state across nodes.
- **Why it matters:** A distributed coordination store relies on strict quorums and stable node membership definitions to prevent split-brain and ensure configuration consistency.
- **Connection to Issue:** Directly relates to why manual cluster.conf modifications and node additions/removals caused Raft metadata instability and missing port/endpoint states.

### Persistent State and Data Directory Management
- **What is it:** Stateful distributed systems store local logs, metadata, and snapshots in persistent data directories.
- **Why it matters:** Stale persistent data on replaced or removed nodes can conflict with new cluster membership definitions if not cleaned up properly.
- **Connection to Issue:** Explains why old nodes persisted in metadata and why clearing the local 'data' directory was required to restore normal cluster operation.

