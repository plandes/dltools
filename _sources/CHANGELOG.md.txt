# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased]


## [0.1.5] - 2021-09-21

### Changed
- Rename `DataframeStash` to `SplitKeyDataframeStash`.
- Split out `FacadePredictApplication` from the `FacadeModelApplication`.

### Added
- Class `AutoSplitDataframeStash` to automatically split (add a column) a
  Pandas dataframe in to training, validation and test datasets.
- Configuration resource library.
- Add a default distribution for `StashSplitKeyContainer`.


## [0.1.4] - 2021-09-07
### Changed
- Upgrade to [zensols.util] version 1.6.0.
- Better model facade write behavior.


## [0.1.3] - 2021-08-07
### Changed
- Fix torch config GPU->CPU copy/dealloc; add outcomes/output in batch.

### Added
- CLI application to facade "glue" `FacadeApplication`.
- Sequence classification: model base class and batch iterator.
- Track direct output/outcomes/logits from model in results.
- More GPU side memory de-allocation.
- Support for float/quotient batch limits.


## [0.1.2] - 2021-04-29
### Changed
- Upgraded to torch 1.8 and `sklearn` 0.24.1.
- Protect deallocation of non-copied (GPU to GPU) batches.
- Warning clean up for `numpy`.
- Better model naming and file/directory name output.
- Clone tensor correctly in 1.7 per warning.

### Added
- Sparse support for size 3 tensors.
- New [zensols.util] 1.5 CLI application interface to facade.
- Summary spreadsheet reporting for results.  This scans a directory for
  results and adds performance metrics in to CSV file for easy reporting across
  multiple models.


## [0.1.1] - 2020-12-29
Maintenance release.
### Changed
- Updated dependencies and tested across Python 3.7, 3.8, 3.9.


## [0.1.0] - 2020-12-10
First fully functional major feature release, which includes batch
persistence/processing, layers, vectorizors, debugging and many other
features/support.  See [documentation] for more information.


## [0.0.6] - 2020-05-11
### Changed
- Upgrade to [zensols.util] 1.2.1 and torch 1.4.0.

### Added
- Type conversion from torch to numpy and sparse types.
- Implementation of sparse matrix encoding and decoding to compensate for
  PyTorch bug with hanging child processing in `multiprocessing` API.
- Key split stash implementation for data set splits.
- Vectorization framework
- Model training and testing framework.
- Notebook example usage.
- Unit tests, for which, now give very good coverage.

### Removed
- Travis build: too time consuming to make CUDA, python and xenial etc. all
  play together nicely.


## [0.0.5] - 2020-05-04

### Added
- Create sparse tensors.


## [0.0.4] - 2020-04-27

### Change
- Travis tests.
- Upgraded to Python 3.7.


## [0.0.3] - 2019-12-14
Data classes are now used so Python 3.7 is now a requirement.

### Added
- Arbitrarily deep linear layer using constant or decay parameter counts.
- Conv2d interface to PyTorch.

### Changed
- Better handling of tensor to memory mapping and device handling in general.


### Removed
- Moved `test.py` from this repository to [zensols.actioncli].


## [0.0.2] - 2019-07-07
### Added
- Tests.


## [0.0.1] - 2019-07-07
### Added
- Initial version.


<!-- links -->
[Unreleased]: https://github.com/plandes/deeplearn/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/plandes/deeplearn/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/plandes/deeplearn/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/plandes/deeplearn/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/plandes/deeplearn/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/plandes/deeplearn/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/plandes/deeplearn/compare/v0.0.6...v0.1.0
[0.0.6]: https://github.com/plandes/deeplearn/compare/v0.0.5...v0.0.6
[0.0.5]: https://github.com/plandes/deeplearn/compare/v0.0.4...v0.0.5
[0.0.4]: https://github.com/plandes/deeplearn/compare/v0.0.3...v0.0.6
[0.0.3]: https://github.com/plandes/deeplearn/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/plandes/deeplearn/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/plandes/deeplearn/compare/v0.0.0...v0.0.1

[zensols.actioncli]: https://github.com/plandes/actioncli
[zensols.util]: https://github.com/plandes/util
[documentation]: https://plandes.github.io/deeplearn/
