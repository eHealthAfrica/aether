/*
 * Copyright (C) 2018 by eHealth Africa : http://www.eHealthAfrica.org
 *
 * See the NOTICE file distributed with this work for additional information
 * regarding copyright ownership.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing,
 * software distributed under the License is distributed on an
 * "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 * KIND, either express or implied.  See the License for the
 * specific language governing permissions and limitations
 * under the License.
 */

// MAX_PAGE_SIZE ==> used as a hack to return all records via api
// calls pending when pagination is fully implemented
export const MAX_PAGE_SIZE = 5000

export const MASKING_ANNOTATION = 'aetherDataClassification'
export const MASKING_PUBLIC = 'public'

export const PROJECTS_URL = '/api/projects/'
export const PIPELINES_URL = '/api/pipelines/'
export const CONTRACTS_URL = '/api/contracts/'
export const KERNEL_URL = '/api/kernel-url/'

export const DATE_FORMAT = 'MMMM DD, YYYY HH:mm'

// pipeline/contract view sections
export const PIPELINE_SECTION_INPUT = 'input'
export const CONTRACT_SECTION_ENTITY_TYPES = 'entityTypes'
export const CONTRACT_SECTION_MAPPING = 'mapping'
export const CONTRACT_SECTION_SETTINGS = 'settings'
