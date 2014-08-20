Benchmarks for Alternate Transport
==================================

## System specs:

* CPU - Core i5
* RAM - 4GB
* OS  - Linux Mint 13

## First run:

### Input

* 5 documents each of size 10MB on the source.
* 5 documents each of size 10MB on the target.

### Transport - ZeroMQ

* Trial 1 - Total time:  19.5338461399
* Trial 2 - Total time:  19.3412210941
* Trial 3 - Total time:  19.3897049427

### Transport - Reference Implementation

* Trial 1 - Total time:  13.00057888
* Trial 2 - Total time:  13.1415770054
* Trial 3 - Total time:  13.0285129547


## Second run:

### Conditions

* Target replica being served behind a wsgi server.

### Input

* 5 documents each of size 1MB on the source.
* 5 documents each of size 1MB on the target.

### Transport - ZeroMQ

* Trial 1 - Total time: 3.59387898445
* Trial 2 - Total time: 3.80425810814
* Trial 3 - Total time: 3.62171292305

### Transport - Reference Implementation

* Trial 1 - Total time:  3.37552595139
* Trial 2 - Total time:  3.08366703987
* Trial 3 - Total time:  3.19187092781
