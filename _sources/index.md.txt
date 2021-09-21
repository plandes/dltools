# DeepZensols Deep Learning Framework

[![PyPI][pypi-badge]][pypi-link]
[![Python 3.7][python37-badge]][python37-link]
[![Python 3.8][python38-badge]][python38-link]
[![Python 3.9][python39-badge]][python39-link]

This deep learning library was designed to provide consistent and reproducible
results.

* See the [full documentation].
* Paper on [arXiv](http://arxiv.org/abs/2109.03383).

Features:
* Easy to configure and framework to allow for programmatic [debugging] of
  neural networks.
* [Reproducibility] of results
  * All [random seed state] is persisted in the trained model files.
  * Persisting of keys and key order across train, validation and test sets.
* Analysis of results with complete metrics available.
* A [vectorization] framework that allows for pickling tensors.
* Additional [layers]:
  * Full [BiLSTM-CRF] and stand-alone [CRF] implementation using easy to
    configure constituent layers.
  * Easy to configure *N* [deep convolution layer] with automatic
    dimensionality calculation and configurable pooling and batch centering.
  * [Convolutional layer factory] with dimensionality calculation.
  * [Recurrent layers] that abstracts RNN, GRU and LSTM.
  * *N* deep [linear layers].
  * Each layer's configurable with activation, dropout and batch normalization.
* [Pandas] integration to [data load], [easily manage] [vectorized features],
  and [report results].
* Multi-process for time consuming CPU feature [vectorization] requiring little
  to no coding.
* Resource and tensor deallocation with memory management.
* [Real-time performance] and loss metrics with plotting while training.
* Thorough [unit test] coverage.
* [Debugging] layers using easy to configure Python logging module and control
  points.

Much of the code provides convenience functionality to [PyTorch].  However,
there is functionality that could be used for other deep learning APIs.


## Documentation

See the [full documentation].


## Obtaining

The easiest way to install the command line program is via the `pip` installer:
```bash
pip3 install zensols.deeplearn
```

Binaries are also available on [pypi].


## Workflow

This package provides a workflow for processing features, training and then
testing a model.  A high level outline of this process follows:
1. Container objects are used to represent and access data as features.
1. Instances of *data points* wrap the container objects.
1. Vectorize the features of each data point in to tensors.
1. Store the vectorized tensor features to disk so they can be retrieved
   quickly and frequently.
1. At train time, load the vectorized features in to memory and train.
1. Test the model and store the results to disk.

To jump right in, see the [examples](#examples) section.  However, it is better
to peruse the in depth explanation with the [Iris example] code follows:
* The initial [data processing], which includes data representation to batch
  creation.
* Creating and configuring the [model].
* Using a [facade] to train, validate and test the model.
* Analysis of [results], including training/validation loss graphs and
  performance metrics.


## Examples

The [Iris example] (also see the [Iris example configuration]) is the most
basic example of how to use this framework.  This example is detailed in the
[workflow](#workflow) documentation in detail.

There are also examples in the form of [Juypter] notebooks as well, which
include the:
* [Iris notebook] data set, which is a small data set of flower dimensions as a
  three label classification,
* [MNIST notebook] for the handwritten digit data set,
* [debugging notebook].


## Attribution

This project, or example code, uses:
* [PyTorch] as the underlying framework.
* Branched code from [Torch CRF](#torch-crf) for the [CRF] class.
* [pycuda] for Python integration with [CUDA].
* [scipy] for scientific utility.
* [Pandas] for prediction output.
* [matplotlib] for plotting loss curves.

Corpora used include:
* [Iris data set]
* [Adult data set]
* [MNIST data set]


### Torch CRF

The [CRF] class was taken and modified from Kemal Kurniawan's [pytorch_crf]
GitHub repository.  See the `README.md` module documentation for more
information.  This module was [forked pytorch_crf] with modifications.
However, the modifications were not merged and the project appears to be
inactive.

**Important**: This project will change to use it as a dependency pending
merging of the changes needed by this project.  Until then, it will remain as a
separate class in this project, which is easier to maintain as the only
class/code is the `CRF` class.

The [pytorch_crf] repository uses the same license as this repository, which
the [MIT License].  For this reason, there are no software/package tainting
issues.


## See Also

The [zensols deepnlp] project is a deep learning utility library for natural
language processing that aids in feature engineering and embedding layers that
builds on this project.


## Citation

If you use this project in your research please use the following BibTeX entry:
```
@article{Landes_DiEugenio_Caragea_2021,
  title={DeepZensols: Deep Natural Language Processing Framework},
  url={http://arxiv.org/abs/2109.03383},
  note={arXiv: 2109.03383},
  journal={arXiv:2109.03383 [cs]},
  author={Landes, Paul and Di Eugenio, Barbara and Caragea, Cornelia},
  year={2021},
  month={Sep}
}
```


## Community

Please star the project and let me know how and where you use this API.
Contributions as pull requests, feedback and any input is welcome.


## Changelog

An extensive changelog is available [here](CHANGELOG.md).


## License

[MIT License]

Copyright (c) 2020 - 2021 Paul Landes


<!-- links -->
[pypi]: https://pypi.org/project/zensols.deeplearn/
[pypi-link]: https://pypi.python.org/pypi/zensols.deeplearn
[pypi-badge]: https://img.shields.io/pypi/v/zensols.deeplearn.svg
[python37-badge]: https://img.shields.io/badge/python-3.7-blue.svg
[python37-link]: https://www.python.org/downloads/release/python-370
[python38-badge]: https://img.shields.io/badge/python-3.8-blue.svg
[python38-link]: https://www.python.org/downloads/release/python-380
[python39-badge]: https://img.shields.io/badge/python-3.9-blue.svg
[python39-link]: https://www.python.org/downloads/release/python-390

[MIT License]: LICENSE.md
[PyTorch]: https://pytorch.org
[Juypter]: https://jupyter.org
[pycuda]: https://pypi.org/project/pycuda/
[CUDA]: https://developer.nvidia.com/cuda-toolkit
[scipy]: https://www.scipy.org
[Pandas]: https://pandas.pydata.org
[matplotlib]: https://matplotlib.org

[pytorch_crf]: https://github.com/kmkurn/pytorch-crf
[forked pytorch_crf]: https://github.com/plandes/pytorch-crf
[zensols.deeplearn.layer.CRF]: api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.crf.CRF
[zensols deepnlp]: https://plandes.github.io/deepnlp

[full documentation]: https://plandes.github.io/deeplearn/index.html
[Iris notebook]: https://github.com/plandes/deeplearn/tree/master/notebook/iris.ipynb
[MNIST notebook]: https://github.com/plandes/deeplearn/tree/master/notebook/mnist.ipynb
[debugging notebook]: https://github.com/plandes/deeplearn/tree/master/notebook/debug.ipynb

[model]: https://plandes.github.io/deeplearn/doc/model.html
[facade]: https://plandes.github.io/deeplearn/doc/facade.html
[results]: https://plandes.github.io/deeplearn/doc/results.html
[data processing]: https://plandes.github.io/deeplearn/doc/preprocess.html
[layers]: https://plandes.github.io/deeplearn/doc/layers.html
[reproducibility]: https://plandes.github.io/deeplearn/doc/results.html#reproducibility
[debugging]: https://plandes.github.io/deeplearn/doc/facade.html#debugging-the-model
[random seed state]: api/zensols.deeplearn.html#zensols.deeplearn.torchconfig.TorchConfig.set_random_seed
[Real-time performance]: https://plandes.github.io/deeplearn/doc/results.html#plotting-loss
[Debugging]: https://plandes.github.io/deeplearn/doc/model.html#debugging
[unit test]: https://github.com/plandes/deeplearn/tree/master/test/python
[vectorization]: https://plandes.github.io/deeplearn/doc/preprocess.html#vectorizers
[Iris example]: https://github.com/plandes/deeplearn/blob/master/test/python/iris/model.py
[Iris example configuration]: https://github.com/plandes/deeplearn/blob/master/test-resources/iris

[Iris data set]: https://archive.ics.uci.edu/ml/datasets/iris
[Adult data set]: http://archive.ics.uci.edu/ml/datasets/Adult
[MNIST data set]: http://yann.lecun.com/exdb/mnist/

[data load]: https://plandes.github.io/deeplearn/api/zensols.dataframe.html?highlight=dataframestash#zensols.dataframe.stash.DataframeStash
[easily manage]: https://plandes.github.io/deeplearn/api/zensols.deeplearn.dataframe.html?highlight=dataframefeaturevectorizermanager#zensols.deeplearn.dataframe.vectorize.DataframeFeatureVectorizerManager
[vectorized features]: https://plandes.github.io/deeplearn/api/zensols.deeplearn.vectorize.html?highlight=seriesencodablefeaturevectorizer#zensols.deeplearn.vectorize.vectorizers.OneHotEncodedEncodableFeatureVectorizer
[report results]: https://plandes.github.io/deeplearn/api/zensols.deeplearn.result.html?highlight=modelresultreporter#zensols.deeplearn.result.report.ModelResultReporter

[Convolutional layer factory]: https://plandes.github.io/deeplearn/api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.conv.ConvolutionLayerFactory
[CRF]: https://plandes.github.io/deeplearn/api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.crf.CRF
[BiLSTM-CRF]: https://plandes.github.io/deeplearn/api/zensols.deeplearn.layer.html?highlight=recurrentcrf#zensols.deeplearn.layer.recurcrf.RecurrentCRF
[Recurrent layers]: https://plandes.github.io/deeplearn/api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.recur.RecurrentAggregation
[linear layers]: https://plandes.github.io/deeplearn/api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.linear.DeepLinear
