###############################################################################
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
###############################################################################
from .common import get_permutation_config


def convert_keras_pooling_core(scope, operator, container, is_global, n_dims,
                               op_type, input_perm_axes, output_perm_axes):
    op = operator.raw_operator
    no_permutation_required = op.data_format == 'channels_first' if hasattr(op, 'data_format') else False

    if no_permutation_required:
        adjusted_pooling_input = operator.inputs[0].full_name
    else:
        adjusted_pooling_input = scope.get_unique_variable_name('input_transposed')
        preprocessor_type = 'Transpose'
        preprocessor_attrs = {'name': scope.get_unique_operator_name(preprocessor_type), 'perm': input_perm_axes}
        container.add_node(preprocessor_type, operator.inputs[0].full_name,
                           adjusted_pooling_input, **preprocessor_attrs)

    op_type_prefix = 'Global' if is_global else ''
    onnx_op_type = "AveragePool" if op_type == 'Avg' else 'MaxPool'
    attrs = {'name': operator.full_name}
    op_version = 10 if container.target_opset >= 10 else 7
    if not is_global:
        attrs['strides'] = list(op.strides)
        attrs['kernel_shape'] = op.pool_size
        attrs['op_version'] = op_version
        # In ONNX opset 10, the ceil_mode attribute was added to local MaxPool and AveragePool
        if container.target_opset >= 10:
            attrs['ceil_mode'] = 0
        if op.padding == 'valid':
            attrs['auto_pad'] = 'VALID'
        elif op.padding == 'same':
            attrs['auto_pad'] = 'SAME_UPPER'
        else:
            raise RuntimeError("Unsupported padding type '{0}'".format(op.padding))

    if no_permutation_required:
        # In this case, the output of our Pool operator just match what Keras produces.
        container.add_node(op_type_prefix + onnx_op_type, adjusted_pooling_input,
                           operator.outputs[0].full_name, **attrs)
    else:
        # Put the output of Pool operator to an intermediate tensor. Laster we will apply a Transpose to match the
        # original Keras output format
        pooling_output_name = scope.get_unique_variable_name('pooling_output')
        container.add_node(op_type_prefix + onnx_op_type, adjusted_pooling_input, pooling_output_name, **attrs)

        # Generate a final Transpose
        postprocessor_type = 'Transpose'
        postprocessor_attrs = {'name': scope.get_unique_operator_name(preprocessor_type), 'perm': output_perm_axes}
        container.add_node(postprocessor_type, pooling_output_name,
                           operator.outputs[0].full_name, **postprocessor_attrs)


def convert_keras_max_pooling_1d(scope, operator, container):
    input_perm_axes, output_perm_axes = get_permutation_config(1)
    convert_keras_pooling_core(scope, operator, container, is_global=False, n_dims=1, op_type='Max',
                               input_perm_axes=input_perm_axes, output_perm_axes=output_perm_axes)


def convert_keras_max_pooling_2d(scope, operator, container):
    input_perm_axes, output_perm_axes = get_permutation_config(2)
    convert_keras_pooling_core(scope, operator, container, is_global=False, n_dims=2, op_type='Max',
                               input_perm_axes=input_perm_axes, output_perm_axes=output_perm_axes)


def convert_keras_max_pooling_3d(scope, operator, container):
    input_perm_axes, output_perm_axes = get_permutation_config(3)
    convert_keras_pooling_core(scope, operator, container, is_global=False, n_dims=3, op_type='Max',
                               input_perm_axes=input_perm_axes, output_perm_axes=output_perm_axes)


def convert_keras_average_pooling_1d(scope, operator, container):
    input_perm_axes, output_perm_axes = get_permutation_config(1)
    convert_keras_pooling_core(scope, operator, container, is_global=False, n_dims=1, op_type='Avg',
                               input_perm_axes=input_perm_axes, output_perm_axes=output_perm_axes)


def convert_keras_average_pooling_2d(scope, operator, container):
    input_perm_axes, output_perm_axes = get_permutation_config(2)
    convert_keras_pooling_core(scope, operator, container, is_global=False, n_dims=2, op_type='Avg',
                               input_perm_axes=input_perm_axes, output_perm_axes=output_perm_axes)


def convert_keras_average_pooling_3d(scope, operator, container):
    input_perm_axes, output_perm_axes = get_permutation_config(3)
    convert_keras_pooling_core(scope, operator, container, is_global=False, n_dims=3, op_type='Avg',
                               input_perm_axes=input_perm_axes, output_perm_axes=output_perm_axes)
