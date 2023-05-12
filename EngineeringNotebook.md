# Engineering Design Choices
## Leader Election, election timeouts, and ties: 
Leader election is a critical aspect of distributed systems like RaftCal, as it ensures that a single server coordinates operations and maintains consistency. However, it also presents several challenges. One such challenge is the possibility of election timeouts being too similar across the servers or too short (tenths of milliseconds), which can lead to contention and frequent leader changes, negatively affecting the system's stability because we want the client to always be able to connect to a leader or always receive from a follower server who the current leader is, but this is difficult during leaderless states.

Additionally, ties can occur when two replicants become candidates at the same time, leading to a split vote and the absence of a clear leader. This situation can result in a prolonged leaderless state and increased latency, as the system must undergo multiple election rounds to resolve the tie and elect a new leader.

### Choice: 
Our design choice involves randomly initializing the election timeouts and heartbeat intervals within a larger range than recommended in the original RAFT paper (400ms - 2s). This approach significantly reduces the likelihood of similar timeouts across servers, decreasing the chances of contention and leader changes and also priotizes the client's ability to consistently connect to a leader.

The primary risk associated with this design choice is the potential for increased latency in the system. A larger election timeout range might result in longer waiting times for leader election, affecting the responsiveness of the application. However, we believe that this trade-off is justified in our project, as it helps ensure the stability of the system and reduces the frequency of leader changes.

By adopting this design choice, we aim to strike a balance between system stability and latency, prioritizing the client's ability to consistently connect to a leader or receive information about the current leader from a follower server. Although this approach may introduce some latency, we believe that the overall benefits of reducing contention and ties in the leader election process outweigh the potential drawbacks.

## Scalability:

As the number of clients and events increases, the system may experience performance issues due to the increasing demands on the leader and replicants. But having multiple backup servers offers several benefits. In the event of server failures, the presence of backup servers ensures that the system can continue operating, providing clients with uninterrupted access to their calendar data. This fault tolerance is essential for maintaining a consistent and reliable user experience. Furthermore, multiple backup servers offer data redundancy, as the calendar events are replicated across all servers. This redundancy protects the data from being lost due to a single server failure and ensures that users can access their calendar data even in the face of server crashes.

### Choice:
 In the design and development of RaftCal, we chose to implement a three-server setup, comprising one leader and two replicant servers. By focusing on a three-server configuration, we were able to concentrate on understanding and implementing the core concepts of the RAFT consensus algorithm. This allowed us to build a functional shared calendar system without getting overwhelmed by the complexities of a larger-scale deployment. The choice of a three-server configuration strikes a balance between system complexity and performance.

While our current design does not address all scalability concerns, such as adding more servers or providing redundancy beyond the two replicant servers, it serves as a solid foundation for further development and exploration. The complexities associated with scaling the system, including adapting the leader election process and ensuring consistent replication across a larger number of servers, can be addressed in future iterations of the project.

## Fault Tolerance: 
RaftCal is designed to be fault-tolerant, with the ability to continue operating as long as one server remains active. However, this poses a problem with the original RAFT algorithm – because when there is only one server what is defined as “majority” and how do we know that there is truly only one server (a server could think that it is the only server)?

### Choice: 
To tackle this issue, we have decided that when a server detects two consecutive drops, it automatically assumes the role of leader. This approach simplifies the leader election process in the case of a single server scenario. However, there is an inherent risk associated with this design choice, especially in a two-server system where both servers believe they are the only remaining server due to disconnection from each other.

In such a situation, the client will attempt to connect to the server with the lower port number first, assuming that server is the leader. While this approach could potentially lead to temporary inconsistencies, we believe that the risk is minimal and does not significantly impact the overall functionality of the client-side application. This is because, upon system reboot, the servers will synchronize their data with the most updated log, which will be the log from the server that the client connected to first.

By making this design choice, we aim to maintain a balance between simplicity and reliability in handling fault tolerance when only one server remains active. This approach allows us to prioritize client-side functionality and ensures a smooth user experience while minimizing the risks associated with potential inconsistencies. Overall, we believe that our design choice is appropriate and makes sense given the constraints and objectives of the RaftCal project.

## Security: 
Protecting the integrity and confidentiality of the calendar data is vital, as users may store sensitive information in their events. Implementing proper authentication and encryption mechanisms to secure the data is an essential challenge.

### Choice:
In our current implementation of RaftCal, we have not incorporated login authentication, encryption, or comprehensive cybersecurity measures. Our primary objective for this project was to explore the implementation of the RAFT consensus algorithm in a practical application, which necessitated a focus on core distributed system concepts rather than an extensive security implementation.

Some potential approaches to enhance security in future versions of RaftCal include:  
Implementing a secure login system with strong password requirements and multi-factor authentication (MFA) can help ensure that only authorized users have access to their calendar data. Moreover we could implement some level of encryption – encrypting calendar data both in transit and at rest can protect the confidentiality and integrity of the information. This could involve using encryption protocols like TLS for data transmission and storage encryption techniques for data at rest on the servers.

## Log Compaction: 
Over time, the log files containing calendar events can grow significantly in size, leading to increased storage requirements and longer startup times. Implementing log compaction strategies to keep the logs manageable is an important challenge.

### Choice:  
In our current implementation of RaftCal, we chose to use the Pickle Dump operation to store the committed calendar events in local memory logs on disk for both the leader and replicant servers. Pickling is a process in which Python objects are serialized into a byte stream, allowing for efficient storage and transfer of complex data structures.

The decision to use Pickle Dump comes with some trade-offs. On one hand, it ensures simplicity and reliability in our system by offering an easy and straightforward way to store and recover data structures. This approach guarantees that the system can reliably recover from crashes and maintain consistency across the servers.

However, there are some risks to this design choice:  
1. Pickle Dump is computationally and time expensive, which can lead to increased latency during log

operations. This may become more pronounced as the log files grow in size over time.

2. As the log files expand, the storage requirements for each server will also increase, potentially affecting system performance and resource allocation.

3. When sending logs over the network, we transfer the pickled representation, which can be data-heavy. This may result in increased network traffic and longer transmission times, especially as the logs grow.

Despite these drawbacks, our design choice to use Pickle Dump was driven by the need to strike a balance between simplicity, reliability, and performance. For the scope of this project, the benefits of an easily implementable and reliable storage solution outweigh the potential issues related to performance and storag