from bravado_core.exception import SwaggerMappingError
# from bravado_core.model import Model
from bravado_core.model import MODEL_MARKER
from bravado_core.marshal import (
    handle_null_value, marshal_schema_object, is_prop_nullable
)
from bravado_core.unmarshal import unmarshal_object
from bravado_core.schema import collapsed_properties
from bravado_core.schema import get_spec_for_prop
from bravado_core.schema import is_dict_like


# patches : bravado_core.marshal.marshal_model
def marshal_model(swagger_spec, model_spec, model_value):
    """Marshal a Model instance into a json-like dict.
    :type swagger_spec: :class:`bravado_core.spec.Spec`
    :type model_spec: dict
    :type model_value: Model instance
    :rtype: dict
    :raises: SwaggerMappingError
    """
    deref = swagger_spec.deref
    model_name = deref(model_spec).get(MODEL_MARKER)
    model_type = swagger_spec.definitions.get(model_name, None)

    if model_type is None:
        raise SwaggerMappingError('Unknown model {0}'.format(model_name))

    if model_value is None:
        return handle_null_value(swagger_spec, model_spec)

    # just convert the model to a dict and feed into `marshal_object` because
    # models are essentially 'type':'object' when marshaled
    if not isinstance(model_value, list):
        object_value = model_value._as_dict()
    else:
        object_value = model_value

    return marshal_object(swagger_spec, model_spec, object_value)


# patches : bravado_core.marshal.marshal_object
def marshal_object(swagger_spec, object_spec, object_value):
    """Marshal a python dict to json dict.
    :type swagger_spec: :class:`bravado_core.spec.Spec`
    :type object_spec: dict
    :type object_value: dict
    :rtype: dict
    :raises: SwaggerMappingError
    """
    deref = swagger_spec.deref

    if object_value is None:
        return handle_null_value(swagger_spec, object_spec)

    if not is_dict_like(object_value):
        return object_value

    object_spec = deref(object_spec)
    required_fields = object_spec.get('required', [])
    properties = collapsed_properties(object_spec, swagger_spec)

    result = {}
    for k, v in object_value.items():

        prop_spec = get_spec_for_prop(
            swagger_spec, object_spec, object_value, k, properties)

        if not prop_spec:
            # Don't marshal when a spec is not available - just pass through
            result[k] = v
            continue

        if v is None and k not in required_fields:
            if not is_prop_nullable(swagger_spec, prop_spec):
                continue

        result[k] = marshal_schema_object(swagger_spec, prop_spec, v)

    return result


# patches : bravado_core.unmarshal.unmarshal_model
def unmarshal_model(swagger_spec, model_spec, model_value):
    """Unmarshal a dict into a Model instance.
    :type swagger_spec: :class:`bravado_core.spec.Spec`
    :type model_spec: dict
    :type model_value: dict
    :rtype: Model instance
    :raises: SwaggerMappingError
    """
    deref = swagger_spec.deref
    model_name = deref(model_spec).get(MODEL_MARKER)
    model_type = swagger_spec.definitions.get(model_name, None)

    if model_type is None:
        raise SwaggerMappingError(
            'Unknown model {0} when trying to unmarshal {1}'
            .format(model_name, model_value))

    if model_value is None:
        return handle_null_value(swagger_spec, model_spec)

    is_bulk = False
    if not is_dict_like(model_value):
        is_bulk = True

    # Check if model is polymorphic
    discriminator = model_spec.get('discriminator')
    if discriminator is not None:
        child_model_name = model_value.get(discriminator, None)
        if child_model_name not in swagger_spec.definitions:
            raise SwaggerMappingError(
                'Unknown model {0} when trying to unmarshal {1}. '
                'Value of {2}\'s discriminator {3} did not match any definitions.'
                .format(child_model_name, model_value, model_name, discriminator)
            )
        model_type = swagger_spec.definitions.get(child_model_name)
        model_spec = model_type._model_spec

    if not is_bulk:
        model_as_dict = unmarshal_object(swagger_spec, model_spec, model_value)
        model_instance = model_type._from_dict(model_as_dict)
        return model_instance

    else:
        res = []
        for item in model_value:
            model_as_dict = unmarshal_object(swagger_spec, model_spec, item)
            model_instance = model_type._from_dict(model_as_dict)
            res.append(model_instance)
        return res
