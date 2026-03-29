Transaction Scheduling & Correctness Analyzer
=============================================

Requirements
------------
Python 3.8 or higher

Project Files
-------------
main.py
parser.py
validator.py
analysis_correctness.py
analysis_serializability.py
schedule_generator.py
model.py

How to Run
----------

1. Open terminal in the project folder

2. Run:

python main.py

3. Enter the number of transactions.

4. Define each transaction using operations such as:

w1[x]   write
r1[x]   read
inc1[x] increment
dec1[x] decrement
c1      commit
a1      abort

Example transaction:

T1: w1[x] r1[y] c1
T2: r2[x] w2[y] c2

5. Choose schedule generation mode:

1 - Serial schedule
2 - Random interleaving
3 - Highly interleaved schedule
4 - Manual schedule input

The system will analyze the schedule and report:

- Conflict serializability
- Precedence graph
- Equivalent serial schedules
- Recoverable (RC)
- ACA
- Strict
- Rigorous
