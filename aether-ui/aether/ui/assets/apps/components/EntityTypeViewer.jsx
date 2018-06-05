import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { generateGUID } from '../utils'

const PropertyList = props => {
  if (!props.fields || !props.fields.length) {
    return (
      <FormattedMessage
        id='entityTypes.entity.empty.properties.message'
        defaultMessage='Entity has no properties'
      />
    )
  }

  return props.fields.map(field => {
    let parent = null
    if (props.parent) {
      parent = `${props.parent}.${field.name}`
    } else {
      parent = field.name
    }

    if (Array.isArray(field.type)) {
      let typeStringOptions = null
      const typeObjectOptions = []
      let isNullable = false
      field.type.forEach(typeItem => {
        if (!typeStringOptions) {
          typeStringOptions = []
        }
        if (typeof typeItem === 'string') {
          if (typeItem === 'null') {
            isNullable = true
          } else {
            typeStringOptions.push(typeItem)
          }          
        } else if (typeof typeItem === 'object') {
          typeStringOptions.push(typeItem.type)
        }
      })
      return PropertyList({
        highlight: props.highlight,
        fields: [{name: field.name, type: typeStringOptions.toString()}],
        name: props.name,
        parent: props.parent,
        isNullable
      })
    } else if (typeof field.type === 'object') {
      return PropertyList({
        highlight: props.highlight,
        fields: field.type.fields || [field.type],
        parent: field.type.fields ? `${parent}.${field.type.name}` : parent,
        name: props.name
      })
    } else {
      const fieldType = field.type

      if (props.parent) {
        const jsonPath = `${props.name}.${props.parent}.${field.name}`
        const className = props.highlight.indexOf(jsonPath) > -1 ? 'entityType-mapped' : ''
        return (
          <li
            key={`${props.parent}.${field.name}`}
            className={className}
            id={`entityType_${jsonPath}`}>
            <span className='name'>{`${props.parent}.${field.name}`}</span>
            <span className='type'> {fieldType === 'enum' ? `${fieldType}: [${field.symbols.toString()}]` : fieldType}</span>
            {props.isNullable ? <span className='type'> (nullable)</span> : null}
          </li>
        )
      } else {
        const jsonPath = `${props.name}.${field.name}`
        const className = props.highlight.indexOf(jsonPath) > -1 ? 'entityType-mapped' : ''
        return (
          <li
            key={field.name}
            className={className}
            id={`entityType_${jsonPath}`}>
            <span className='name'>{field.name}</span>
            <span className='type'> {fieldType}</span>
            {props.isNullable ? <span className='type'> (nullable)</span> : null}
          </li>
        )
      }
    }
  })
}

const EntityType = props => {
  return (
    <div className='entity-type'>
      <h2 className='title'>{props.name}</h2>
      <ul className='properties'>
        <PropertyList
          highlight={props.highlight}
          fields={props.fields}
          name={props.name}
        />
      </ul>
    </div>
  )
}

class EntityTypeViewer extends Component {
  iterateTypes (entityTypes) {
    if (!entityTypes || !entityTypes.length) {
      return (
        <div className='hint'>
          <FormattedMessage
            id='entityTypes.entity.invalid.schema'
            defaultMessage='No Entity Types added to this pipeline yet.'
          />
        </div>
      )
    }

    return entityTypes.map(entityType => {
      if (entityType.name && entityType.fields) {
        return (
          <EntityType
            key={entityType.name}
            highlight={this.props.highlight}
            name={entityType.name}
            fields={entityType.fields}
          />
        )
      } else {
        return (
          <div className='hint' key={generateGUID()}>
            <FormattedMessage
              id='entityTypes.entity.invalid.message'
              defaultMessage='Invalid entity type'
            />
          </div>
        )
      }
    })
  }

  render () {
    if (!this.props.schema) {
      return (
        <div className='hint'>
          <FormattedMessage
            id='entityTypes.entity.empty.message'
            defaultMessage='No entity types added to this pipeline yet.'
          />
        </div>
      )
    }

    return (
      <div className='entity-types-schema'>
        { this.iterateTypes(this.props.schema) }
      </div>
    )
  }
}

export default EntityTypeViewer
