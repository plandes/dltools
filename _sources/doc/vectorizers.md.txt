# Vectorizers

Please first read the [vectorizers] section first.

The set of vectorizers included with this package are listed below:

* [IdentityEncodableFeatureVectorizer]: An identity vectorizer, which encodes
  tensors verbatim, or concatenates a list of tensors in to one tensor of the
  same dimension.
* [CategoryEncodableFeatureVectorizer]: A base class that vectorizies nominal
  categories in to integer indexes.
* [NominalEncodedEncodableFeatureVectorizer]: Map each label to a nominal,
  which is useful for class labels.
* [OneHotEncodedEncodableFeatureVectorizer]: Vectorize from a list of nominals.
  This is useful for encoding labels for the categorization machine learning
  task.
* [AggregateEncodableFeatureVectorizer]: Use another vectorizer to vectorize
  each instance in an iterable.  Each iterable is then concatenated in to a
  single tensor on decode.
* [MaskTokenContainerFeatureVectorizer]: Creates masks where the first N
  elements of a vector are 1's with the rest 0's.
* [SeriesEncodableFeatureVectorizer]: Vectorize a Pandas series, such as a list
  of rows.  This vectorizer has an undefined shape since both the number of
  columns and rows are not specified at runtime.
* [AttributeEncodableFeatureVectorizer]: Vectorize a iterable of floats.  This
  vectorizer has an undefined shape since both the number of columns and rows
  are not specified at runtime.


<!-- links -->

[vectorizers]: https://plandes.github.io/deeplearn/doc/preprocess.html#vectorizers
[IdentityEncodableFeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.vectorizers.IdentityEncodableFeatureVectorizer
[CategoryEncodableFeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.vectorizers.CategoryEncodableFeatureVectorizer
[NominalEncodedEncodableFeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.vectorizers.NominalEncodedEncodableFeatureVectorizer
[OneHotEncodedEncodableFeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.vectorizers.OneHotEncodedEncodableFeatureVectorizer
[AggregateEncodableFeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.vectorizers.AggregateEncodableFeatureVectorizer
[MaskTokenContainerFeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.vectorizers.MaskTokenContainerFeatureVectorizer
[SeriesEncodableFeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.vectorizers.SeriesEncodableFeatureVectorizer
[AttributeEncodableFeatureVectorizer]: ../api/zensols.deeplearn.vectorize.html#zensols.deeplearn.vectorize.vectorizers.AttributeEncodableFeatureVectorizer
