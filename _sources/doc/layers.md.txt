# Layers

Please first read the [class naming parlance] section first.

The set of layers, layer settings and layer factories included with this
package are listed below:

* Convolution:
  * [ConvolutionLayerFactory]: Create convolution layers.
  * [PoolFactory]: Create a 2D max pool and output it's shape.
  * [MaxPool2dFactory]: Create a 2D max pool and output it's shape.
  * [MaxPool1dFactory]: Create a 1D max pool and output it's shape.
* Linear:
  * [DeepLinearNetworkSettings]: Settings for a deep fully connected network.
  * [DeepLinear]: A layer that has contains one more nested layers, including
    batch normalization and activation.
* Recurrent (RNN, LSTM, GRU):
  * [RecurrentAggregationNetworkSettings]: Settings for a recurrent neural network.
  * [RecurrentAggregation]: A recurrent neural network model with an output
    aggregation.
* Conditional Random Fields:
  * [CRF]: Conditional random field (pure [PyTorch] `nn.Module`).
  * [RecurrentCRFNetworkSettings]: Settings for a recurrent neural network.
  * [RecurrentCRF]: Adapt a [CRF] module using the framework based
    [BaseNetworkModule] class.


<!-- links -->
[PyTorch]: https://pytorch.org
[class naming parlance]: model.html#class-name-parlance

[ConvolutionLayerFactory]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.conv.ConvolutionLayerFactory
[PoolFactory]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.conv.PoolFactory
[MaxPool2dFactory]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.conv.MaxPool2dFactory
[MaxPool1dFactory]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.conv.MaxPool1dFactory

[BaseNetworkModule]: ../api/zensols.deeplearn.model.html#zensols.deeplearn.model.module.BaseNetworkModule
[DeepLinearNetworkSettings]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.linear.DeepLinearNetworkSettings
[DeepLinear]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.linear.DeepLinear

[RecurrentAggregationNetworkSettings]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.recur.RecurrentAggregationNetworkSettings
[RecurrentAggregation]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.recur.RecurrentAggregation

[CRF]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.crf.CRF
[RecurrentCRFNetworkSettings]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.recurcrf.RecurrentCRFNetworkSettings
[RecurrentCRF]: ../api/zensols.deeplearn.layer.html#zensols.deeplearn.layer.recurcrf.RecurrentCRF
