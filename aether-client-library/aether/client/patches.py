# Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
#
# See the NOTICE file distributed with this work for additional information
# regarding copyright ownership.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from bravado_core.marshal import (
    _marshal_object as original__marshal_object,
)
from bravado_core.unmarshal import (
    _unmarshal_object as original__unmarshal_object,
)
from bravado_core.schema import is_list_like


# patches : bravado_core.marshal._marshal_object
def patched__marshal_object(
    swagger_spec,
    properties_to_marshaling_function,
    additional_properties_marshaling_function,
    discriminator_property,
    possible_discriminated_type_name_to_model,
    required_properties,
    nullable_properties,
    model_value,
):
    if is_list_like(model_value):
        return [
            original__marshal_object(
                swagger_spec,
                properties_to_marshaling_function,
                additional_properties_marshaling_function,
                discriminator_property,
                possible_discriminated_type_name_to_model,
                required_properties,
                nullable_properties,
                value,
            )
            for value in model_value
        ]

    return original__marshal_object(
        swagger_spec,
        properties_to_marshaling_function,
        additional_properties_marshaling_function,
        discriminator_property,
        possible_discriminated_type_name_to_model,
        required_properties,
        nullable_properties,
        model_value,
    )


# patches : bravado_core.unmarshal._unmarshal_object
def patched__unmarshal_object(
    swagger_spec,
    model_type,
    properties_to_unmarshaling_function,
    additional_properties_unmarshaling_function,
    properties_to_default_value,
    discriminator_property,
    possible_discriminated_type_name_to_model,
    model_value,
):
    if is_list_like(model_value):
        return [
            original__unmarshal_object(
                swagger_spec,
                model_type,
                properties_to_unmarshaling_function,
                additional_properties_unmarshaling_function,
                properties_to_default_value,
                discriminator_property,
                possible_discriminated_type_name_to_model,
                value,
            )
            for value in model_value
        ]

    return original__unmarshal_object(
        swagger_spec,
        model_type,
        properties_to_unmarshaling_function,
        additional_properties_unmarshaling_function,
        properties_to_default_value,
        discriminator_property,
        possible_discriminated_type_name_to_model,
        model_value,
    )
