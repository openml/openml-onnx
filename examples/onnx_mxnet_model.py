"""
ONNX model example
==================

An example of a sequential network that solves a supervised classification task used
 as an OpenML flow. Uses MXNet as backend.
"""
import openml
import openml_onnx
import onnx
import os
import mxnet as mx
import mxnet.contrib.onnx as onnx_mxnet


ONNX_FILE_PATH_DEFAULT = 'model.onnx'
MXNET_PARAMS_PATH_DEFAULT = './model-0001.params'
MXNET_SYMBOL_PATH_DEFAULT = './model-symbol.json'

############################################################################
# Obtain task with training data
task = openml.tasks.get_task(10101)
X, y = task.get_X_and_y()
train_indices, test_indices = task.get_train_test_split_indices(
    repeat=0, fold=0, sample=0)
X_train = X[train_indices]
y_train = y[train_indices]
X_test = X[test_indices]
y_test = y[test_indices]
############################################################################

############################################################################
# Compute shapes of input and output
output_length = len(task.class_labels)
input_length = X_train.shape[1]

# Create MXNet Variables
data = mx.sym.var('data')
label = mx.sym.var('softmax_label')

# Create the MXNet Module API model
bnorm = mx.sym.BatchNorm(data=data)
fc1 = mx.sym.FullyConnected(data=bnorm, num_hidden=1024)
act1 = mx.sym.Activation(data=fc1, act_type="relu")
drop1 = mx.sym.Dropout(data=act1, p=0.4)
fc2 = mx.sym.FullyConnected(data=drop1, num_hidden=output_length)
mlp = mx.sym.SoftmaxOutput(data=fc2, name='softmax', label=label)
mlp_model = mx.mod.Module(symbol=mlp, context=mx.cpu())

data_shapes = [('data', X_train.shape)]
label_shapes = [('softmax_label', y_train.shape)]

# Bind and initialize parameters
mlp_model.bind(data_shapes=data_shapes, label_shapes=label_shapes)
mlp_model.init_params(mx.init.Xavier())

# Save the parameters and symbol to files
mlp_model.save_params(MXNET_PARAMS_PATH_DEFAULT)
mlp.save(MXNET_SYMBOL_PATH_DEFAULT)

# Export the ONNX specification of the model, using the parameters and symbol files
onnx_mxnet.export_model(
    sym=MXNET_SYMBOL_PATH_DEFAULT,
    params=MXNET_PARAMS_PATH_DEFAULT,
    input_shape=[(64, input_length)],
    onnx_file_path=ONNX_FILE_PATH_DEFAULT)
############################################################################

############################################################################
# Load ONNX file and remove files
model = onnx.load_model(ONNX_FILE_PATH_DEFAULT)
if os.path.exists(MXNET_PARAMS_PATH_DEFAULT):
    os.remove(MXNET_PARAMS_PATH_DEFAULT)
if os.path.exists(MXNET_SYMBOL_PATH_DEFAULT):
    os.remove(MXNET_SYMBOL_PATH_DEFAULT)
if os.path.exists(ONNX_FILE_PATH_DEFAULT):
    os.remove(ONNX_FILE_PATH_DEFAULT)
############################################################################
# Run the model on the task (requires an API key).
run = openml.runs.run_model_on_task(model, task, avoid_duplicate_runs=False)
# Publish the experiment on OpenML (optional, requires an API key).
run.publish()

print('URL for run: %s/run/%d' % (openml.config.server, run.run_id))

############################################################################
