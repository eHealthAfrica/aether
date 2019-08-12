/*
 * Copyright (C) 2019 by eHealth Africa : http://www.eHealthAfrica.org
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

/* global describe, it, expect */

import React from 'react'
import { mountWithIntl } from 'enzyme-react-intl'

import { mockInputSchema } from '../../tests/mock'
import { AvroSchemaViewer } from '../components'

describe('AvroSchemaViewer', () => {
  it('should render an empty avro schema viewer', () => {
    const component = mountWithIntl(<AvroSchemaViewer />)
    expect(component.text())
      .toContain('Your AVRO schema will be displayed here once you have added a valid source.')
  })

  it('should take a invalid avro schema and render an invalid error message', () => {
    const inputSchemaWithoutName = {
      type: 'record',
      fields: []
    }

    const component = mountWithIntl(<AvroSchemaViewer schema={inputSchemaWithoutName} />)
    expect(component.text()).toContain('You have provided an invalid AVRO schema.')
  })

  it('should take a non-record avro schema and render an invalid error message', () => {
    const inputSchemaNoRecord = {
      name: 'id',
      type: 'string'
    }

    const component = mountWithIntl(<AvroSchemaViewer schema={inputSchemaNoRecord} />)
    expect(component.text()).toContain('Initial AVRO schema type can only be of type "record".')
  })

  it('should take a valid avro schema and highlight the indicated fields', () => {
    const component = mountWithIntl(
      <AvroSchemaViewer
        schema={mockInputSchema}
        highlight={{ '$.id': 1, '$.dictionary.code': 2 }}
        pathPrefix='$'
        className='input-schema'
      />
    )

    expect(component.find('[data-qa="$.id"]').html())
      .toContain('<div class="input-schema-mapped-1 field"><span class="name">id</span>')
    expect(component.find('[data-qa="$.dictionary.code"]').html())
      .toContain('<div class="input-schema-mapped-2 field"><span class="name">code</span>')
  })

  it('should take a valid avro schema and render an avro visualizer', () => {
    const component = mountWithIntl(
      <AvroSchemaViewer schema={mockInputSchema} />
    )

    expect(component.find('[data-qa^="group-title-"]').length).toEqual(1)

    // PRIMITIVES

    const idDiv = component.find('[data-qa="id"]').html()
    expect(idDiv).toContain('<div class=" field">')
    expect(idDiv).not.toContain('<i class="fas fa-lock"></i>') // public
    expect(idDiv).toContain('<span class="name">id</span>')
    expect(idDiv).toContain('<span class="type">string</span>')

    const textDiv = component.find('[data-qa="text"]').html()
    expect(textDiv).toContain('<div class=" field">')
    expect(textDiv).toContain('<span class="name">text</span>')
    expect(textDiv).toContain('<span class="type">string (nullable)</span>')

    const choicesDiv = component.find('[data-qa="choices"]').html()
    expect(choicesDiv).toContain('<div class=" field">')
    expect(choicesDiv).toContain('<span class="name">choices</span>')
    expect(choicesDiv).toContain('<span class="type">enum (a, b)</span>')

    // RECORDS

    const dictionaryDiv = component.find('[data-qa="dictionary"]').html()
    expect(dictionaryDiv).toContain('<div data-qa="dictionary" class="group">')
    expect(dictionaryDiv).toContain('<div class=" group-title">')
    expect(dictionaryDiv).toContain('<span class="name">dictionary</span>')
    expect(dictionaryDiv).toContain('<span class="type">record</span>')

    const dictionaryCodeDiv = component.find('[data-qa="dictionary.code"]').html()
    expect(dictionaryCodeDiv).toContain('<div class=" field">')
    expect(dictionaryCodeDiv).toContain('<span class="name">code</span>')
    expect(dictionaryCodeDiv).toContain('<span class="type">int</span>')

    const listNumbersDiv = component.find('[data-qa="list_of_numbers"]').html()
    expect(listNumbersDiv).toContain('<div class=" field">')
    expect(listNumbersDiv).toContain('<span class="name">list_of_numbers</span>')
    expect(listNumbersDiv).toContain('<span class="type">array [union: int, boolean (nullable)]</span>')

    // ARRAYS

    const listTextsDiv = component.find('[data-qa="list_of_texts"]').html()
    expect(listTextsDiv).toContain('<div class=" field">')
    expect(listTextsDiv).toContain('<span class="name">list_of_texts</span>')
    expect(listTextsDiv).toContain('<span class="type">array [string]</span>')

    const listDictionariesDiv = component.find('[data-qa="list_of_dictionaries"]').html()
    expect(listDictionariesDiv).toContain('<div class=" field">')
    expect(listDictionariesDiv).toContain('<span class="name">list_of_dictionaries</span>')
    expect(listDictionariesDiv).toContain('<span class="type">array [record]</span>')

    const listDictionariesWordDiv = component.find('[data-qa="list_of_dictionaries.#.word"]').html()
    expect(listDictionariesWordDiv).toContain('<div class=" field">')
    expect(listDictionariesWordDiv).toContain('<span class="name">word</span>')
    expect(listDictionariesWordDiv).toContain('<span class="type">string</span>')

    const listDictionariesMeaningDiv = component.find('[data-qa="list_of_dictionaries.#.meaning"]').html()
    expect(listDictionariesMeaningDiv).toContain('<div class=" field">')
    expect(listDictionariesMeaningDiv).toContain('<span class="name">meaning</span>')
    expect(listDictionariesMeaningDiv).toContain('<span class="type">string</span>')

    // MAPS

    const mapPrimitivesDiv = component.find('[data-qa="mapping_primitives"]').html()
    expect(mapPrimitivesDiv).toContain('<div class=" field">')
    expect(mapPrimitivesDiv).toContain('<span class="name">mapping_primitives</span>')
    expect(mapPrimitivesDiv).toContain('<span class="type">map {float} (nullable)</span>')

    const mapDictionariesDiv = component.find('[data-qa="mapping_dictionaries"]').html()
    expect(mapDictionariesDiv).toContain('<div class=" field">')
    expect(mapDictionariesDiv).toContain('<span class="name">mapping_dictionaries</span>')
    expect(mapDictionariesDiv).toContain('<span class="type">map {record}</span>')

    const mapDictionariesXDiv = component.find('[data-qa="mapping_dictionaries.#.x"]').html()
    expect(mapDictionariesXDiv).toContain('<div class=" field">')
    expect(mapDictionariesXDiv).toContain('<span class="name">x</span>')
    expect(mapDictionariesXDiv).toContain('<span class="type">double</span>')

    const mapDictionariesYDiv = component.find('[data-qa="mapping_dictionaries.#.y"]').html()
    expect(mapDictionariesYDiv).toContain('<div class=" field">')
    expect(mapDictionariesYDiv).toContain('<span class="name">y</span>')
    expect(mapDictionariesYDiv).toContain('<span class="type">float</span>')

    // UNIONS

    const unionPrimitivesDiv = component.find('[data-qa="primitive_union"]').html()
    expect(unionPrimitivesDiv).toContain('<div class=" field">')
    expect(unionPrimitivesDiv).toContain('<span class="name">primitive_union</span>')
    expect(unionPrimitivesDiv).toContain('<span class="type">union: int, string (nullable)</span>')

    const unionComplexDiv = component.find('[data-qa="complex_union"]').html()
    expect(unionComplexDiv).toContain('<div class=" group-title">')
    expect(unionComplexDiv).toContain('<span class="name">complex_union</span>')
    expect(unionComplexDiv).toContain('<span class="type">union (nullable)</span>')

    const unionComplexBooleanDiv = component.find('[data-qa="complex_union.1"]').html()
    expect(unionComplexBooleanDiv).toContain('<div class=" field">')
    expect(unionComplexBooleanDiv).toContain('<span class="name">1</span>')
    expect(unionComplexBooleanDiv).toContain('<span class="type">boolean</span>')

    const unionComplexStringDiv = component.find('[data-qa="complex_union.2"]').html()
    expect(unionComplexStringDiv).toContain('<div class=" field">')
    expect(unionComplexStringDiv).toContain('<span class="name">2</span>')
    expect(unionComplexStringDiv).toContain('<span class="type">string</span>')

    const unionComplexRecordDiv = component.find('[data-qa="complex_union.3"]').html()
    expect(unionComplexRecordDiv).toContain('<div class=" group-title">')
    expect(unionComplexRecordDiv).toContain('<span class="name">3</span>')
    expect(unionComplexRecordDiv).toContain('<span class="type">record</span>')

    // Extended types and non public

    const locationDiv = component.find('[data-qa="location"]').html()
    expect(locationDiv).toContain('<div data-qa="location" class="group">')
    expect(locationDiv).toContain('<div class=" group-title">')
    expect(locationDiv).toContain('<i class="fas fa-lock"></i>') // restricted
    expect(locationDiv).toContain('<span class="name">location</span>')
    expect(locationDiv).toContain('<span class="type">geopoint (nullable)</span>') // not record

    const timestampDiv = component.find('[data-qa="timestamp"]').html()
    expect(timestampDiv).toContain('<div data-qa="timestamp" class="group">')
    expect(timestampDiv).toContain('<div class=" field">')
    expect(timestampDiv).toContain('<span class="name">timestamp</span>')
    expect(timestampDiv).toContain('<span class="type">dateTime</span>') // not string

    const updatedAtDiv = component.find('[data-qa="updated_at"]').html()
    expect(updatedAtDiv).toContain('<div data-qa="updated_at" class="group">')
    expect(updatedAtDiv).toContain('<div class=" field">')
    expect(updatedAtDiv).toContain('<span class="name">updated_at</span>')
    expect(updatedAtDiv).toContain('<span class="type">dateTime (nullable)</span>') // not string
  })

  it('should take a valid avro schema and render an avro visualizer without nested fields', () => {
    const component = mountWithIntl(
      <AvroSchemaViewer schema={mockInputSchema} hideChildren />
    )

    expect(component.find('[data-qa^="group-title-"]').length).toEqual(1)

    // 1st level

    const idDiv = component.find('[data-qa="id"]').html()
    expect(idDiv).toContain('<div class=" field">')
    expect(idDiv).toContain('<span class="name">id</span>')
    expect(idDiv).toContain('<span class="type">string</span>')

    const dictionaryDiv = component.find('[data-qa="dictionary"]').html()
    expect(dictionaryDiv).toContain('<div data-qa="dictionary" class="group">')
    expect(dictionaryDiv).toContain('<div class=" field">')
    expect(dictionaryDiv).toContain('<span class="name">dictionary</span>')
    expect(dictionaryDiv).toContain('<span class="type">record</span>')

    // 2nd Level
    expect(component.find('[data-qa="dictionary.code"]')).toEqual({})

    const locationDiv = component.find('[data-qa="location"]').html()
    expect(locationDiv).toContain('<div data-qa="location" class="group">')
    expect(locationDiv).toContain('<div class=" field">')
    expect(locationDiv).toContain('<i class="fas fa-lock"></i>')
    expect(locationDiv).toContain('<span class="name">location</span>')
    expect(locationDiv).toContain('<span class="type">geopoint (nullable)</span>')
  })
})
