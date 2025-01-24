# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased]


## [1.13.3] - 2025-01-24
### Changed
- Add missing dependency requirement for multi-label stratification.


## [1.13.2] - 2025-01-23
### Changed
- Fix bug missing result context when predicting.


## [1.13.1] - 2025-01-20
### Changed
- Fix bug in CLI where batches files failed to materialize.
- Fix PyTorch CUDA tensor instantiation warning.


## [1.13.0] - 2025-01-11
### Removed
- `PredictionsDataFrameFactory.metrics_dataframe`, instead use
  `PredictionsDataFrameFactory.metrics_dataframe_describer.df`.
- `ModelFacade.get_predictions`, instead use `get_predictions_factory`.
- Support for Python 3.10.

### Added
- Cross-fold validation functionality and command-line interface.

### Changed
- Consolidated command-line reporting actions and make reporting options
  consistent.
- Moved specialized token classification predictions dataframe creation
  behavior from `ModelFacade` to `PredictionsDataFrameFactory`.
- Complete refactoring of the convolutional (1 and 2D) layer and calculation.
  The 1D calculation was added for both convolution and pool layer output
  shapes.  The layer factory now also create batch normalization layers and
  compute output convolution and pool output shapes for stacked CNN layers.
- Upgraded to [zensols.util] version 1.15.


## [1.12.0] - 2024-10-14
### Changed
- CLI formatting and file options for training, testing and reporting on
  models.
- Layers expect a torch configuration to fix a model quantization issue.
- Disable fp16 error when creating numpy sparse matrices.


## [1.11.2] - 2024-05-11
### Added
- A new feature to update previously trained model distribution's
  configuration.
- Moved the batch size resource library configuration to `default.conf`.

### Changed
- Moved batch size in resource library `batch.conf` to `default.conf`.


## [1.11.1] - 2024-03-14
### Changed
- Fix missing weighted classification metrics in JSON.


## [1.11.0] - 2024-03-07
### Added
- A model client (`ModelUnpacker`) that uses a bundled and downloaded model
  packaged with `ModelPacker`.  It allows two separate code bases to train the
  model and inference with it.
- A feature to turn off saving results (`ModelResults`) with model, which can
  potentially slow training and bloat models.
- A feature to store the results as a string with the model when the
  `ModelResults` is not saved with it.  These results are accessible in
  packaged models.

### Changed
- Move `TclError` to fix Python bailing if not compiled with Tcl/Tk
  (`tkinter`).
- Fix accuracy "N out of total" accuracy reporting metrics.


## [1.10.0] - 2024-02-27
### Added
- Model signifiance testing module `zensols.deeplearn.result.hypsig`.
- Data sanity checks on predictions when creating prediction dataframes.

### Changed
- Move CLI application imports to method level for faster importing.
- Fold `zensols.deeplearn.cli.app` into `zensols.deeplearn.cli`.  Since `app`
  was imported into the `cli` name space, this is backward compatible for apps
  that doesn't fully qualify.
- More flexible configuration options for `ModelFacade` prediction dataframe
  factory.
- Fix CLI batch action ignoring the `limit` argument.


## [1.9.0] - 2023-12-05
### Changed
- Upgrade to PyTorch 2.1.1, numpy 1.25, scipy 1.9, scikit-learn 1.3, pandas
  2.1, and [zensols.util] 1.14.
- Unit and integration test fixes.

### Added
- Support for Python 3.11.
- Multiple CUDA configuration support.

### Removed
- Support for Python 3.9.


## [1.8.1] - 2023-08-16
### Added
- A feature to *inject* application (or any) configuration into a previously
  packed or persisted model via `ModelManager`.
- `SubsetConfig`: subsets the application configuration
- A command-line option on the `FacadeApplication`'s `info` action that
  specifies the model path to allow a dump of the (packed) model's persisted
  configuration.


## [1.8.0] - 2023-08-16
Downstream moderate risk update release.

### Changed
- Set model type in `TorchConfig.to` only if its comparable and different.
- Upgrade to [zensols.util] v1.13.0.


## [1.7.0] - 2023-06-09
## Changes
- Upgraded [scipy] from 1.8.1 to 1.9.3.


## [1.6.1] - 2023-06-07
### Added
- Use of [zensols.datdesc] model output to create LaTeX tables.

### Changed
- Upgrade from torch 1.12 to torch 1.13.
- `TorchConfig` allows specific torch device name initialization, which is useful for
  macOS `mps` devices.


## [1.6.0] - 2023-01-23
### Added
- `SplitKeyContainer` write method for concrete subclasses.

### Changed
- Updated [zensols.util] to 1.12.0.
- Type hints and code clean up.


## [1.5.2] - 2022-11-06
### Changed
- Add batch size to output directory to allow changes without re-batching
  previous batch size configurations.
- Bug fix to validation metrics reporting.


## [1.5.1] - 2022-10-01
### Changed
- Upgrade `zensols.install`.


## [1.5.0] - 2022-10-01
### Removed
- Remove mask creation in aggregate vectorizer.  Use mask vectorizer instead.

### Added
- Added model packaging API.
- Added `Configurable` that reads from a CSV file with Pandas for nominal model
  labels.


## [1.4.0] - 2022-08-06
### Changed
- Upgrade a significant portion of the dependent libraries.


## [1.3.0] - 2022-06-14
This is primarily a refactoring release to simplify the API and examples.

### Added
- Feature creation resource library.
- Zensols installer and dependency for resource library adds.

### Changed
- Initialize PyTorch system from the `zensols.deepnlp` module.
- Stash prime chain fixes.
- Module logging uses calling logger when not provided.
- Add stratified split app reporting from facade app when available.
- Simplify facade application manager for Jupyter notebooks.
- Memory leak fixes in CLI facade application.
- Split off batch from info facade application.
- More error information for missing dataset splits.
- Fix batch feature mapping for prediction.

### Removed
- The `zensols.deeplearn.plot` module.


## [1.2.0] - 2022-05-15
### Added
- New dynamic batch mapping that no longer requires it to be hard coded in a
  Python source file.

### Changed
- Rename gradient norm to gradient scaling in `ModelSettings`.
- Minor bug fixes to results API.


## [1.1.1] - 2022-05-04
### Changed
- Fix pinned requirements.


## [1.1.0] - 2022-05-04
### Added
- Add label prediction metric calculations.
- Add split, label and key access as a Pandas dataframe.
- Create support for sequence based predictions as a Pandas dataframe.
- Add PyTorch `CrossEntryLoss` ignore index padding

### Changed
- Bug fixes and clean up warnings.
- Recurrent CRF network uses new network settings factory method.
- Remove HuggingFace schedule warnings.
- Default `OneHotEncodedFeatureDocumentVectorizer.optimize_bools = True` is
  needed as the default has been removed.
- Move model name configuration from `ModelExecutor` to `ModelSettings`.
- Guard on missing vectorizers.
- Move name from executor to model settings.


## [1.0.0] - 2022-02-12
Stable release

### Added
- Added observer pattern for model facade, execution and trainer.

### Changed
- Resource library clean up.
- Torch GPU memory reporting bug fix.
- Terminal progress bar fixes.


## [0.1.8] - 2022-01-25
### Changed
- PyTorch upgrade API bug fix.


## [0.1.7] - 2022-01-25
### Changes
- Upgrade to torch 1.9.
- Remove dependency on `pycuda`.
- Suppress `numpy` warnings from results reporting module, PyTorch start up and
  MNIST test cases.
- Better CUDA memory debugging/profiling.


## [0.1.6] - 2021-10-22
### Added
- Much more documentation.

### Changed
- Upgrade to new zensols.util import semantics.

### Removed
- Learning rate parameter from resource library.  It is better for the client
  to be forced to set it to avoid ambiguous spurious settings.
- DeepZensols NLP classification configuration that doesn't belong in this
  package.


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
- Upgrade to [zensols.util] 1.3.0 and torch 1.4.0.

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
[Unreleased]: https://github.com/plandes/deeplearn/compare/v1.13.3...HEAD
[1.13.3]: https://github.com/plandes/deeplearn/compare/v1.13.2...v1.13.3
[1.13.2]: https://github.com/plandes/deeplearn/compare/v1.13.1...v1.13.2
[1.13.1]: https://github.com/plandes/deeplearn/compare/v1.13.0...v1.13.1
[1.13.0]: https://github.com/plandes/deeplearn/compare/v1.12.0...v1.13.0
[1.12.0]: https://github.com/plandes/deeplearn/compare/v1.11.2...v1.12.0
[1.11.2]: https://github.com/plandes/deeplearn/compare/v1.11.1...v1.11.2
[1.11.1]: https://github.com/plandes/deeplearn/compare/v1.11.0...v1.11.1
[1.11.0]: https://github.com/plandes/deeplearn/compare/v1.10.0...v1.11.0
[1.10.0]: https://github.com/plandes/deeplearn/compare/v1.9.0...v1.10.0
[1.9.0]: https://github.com/plandes/deeplearn/compare/v1.8.1...v1.9.0
[1.8.1]: https://github.com/plandes/deeplearn/compare/v1.8.0...v1.8.1
[1.8.0]: https://github.com/plandes/deeplearn/compare/v1.7.0...v1.8.0
[1.7.0]: https://github.com/plandes/deeplearn/compare/v1.6.1...v1.7.0
[1.6.1]: https://github.com/plandes/deeplearn/compare/v1.6.0...v1.6.1
[1.6.0]: https://github.com/plandes/deeplearn/compare/v1.5.2...v1.6.0
[1.5.2]: https://github.com/plandes/deeplearn/compare/v1.5.1...v1.5.2
[1.5.1]: https://github.com/plandes/deeplearn/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/plandes/deeplearn/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/plandes/deeplearn/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/plandes/deeplearn/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/plandes/deeplearn/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/plandes/deeplearn/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/plandes/deeplearn/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/plandes/deeplearn/compare/v0.1.8...v1.0.0
[0.1.8]: https://github.com/plandes/deeplearn/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/plandes/deeplearn/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/plandes/deeplearn/compare/v0.1.5...v0.1.6
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
[zensols.datdesc]: https://github.com/plandes/datdesc
[documentation]: https://plandes.github.io/deeplearn/
[scipy]: https://scipy.org
