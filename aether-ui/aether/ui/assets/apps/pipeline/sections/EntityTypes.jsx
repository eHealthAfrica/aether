import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { connect } from 'react-redux'
import avro from 'avro-js'

import { EntityTypeViewer } from '../../components'
import { deepEqual } from '../../utils'
import { updatePipeline } from '../redux'

class EntityTypes extends Component {
  constructor (props) {
    super(props)

    this.state = {
      entityTypesSchema: this.parseProps(props),
      error: null
    }
  }

  componentWillReceiveProps (nextProps) {
    this.setState({
      entityTypesSchema: this.parseProps(nextProps),
      error: null
    })
  }

  parseProps (props) {
    const { entity_types: entityTypes } = props.selectedPipeline
    return entityTypes.length ? JSON.stringify(entityTypes, 0, 2) : ''
  }

  onSchemaTextChanged (event) {
    this.setState({
      entityTypesSchema: event.target.value
    })
  }

  notifyChange (event) {
    event.preventDefault()

    try {
      // validate schemas
      const schemas = JSON.parse(this.state.entityTypesSchema)
      this.props.updatePipeline({ ...this.props.selectedPipeline, entity_types: schemas })
    } catch (error) {
      this.setState({ error: error.message })
    }
  }

  hasChanged () {
    try {
      const schemas = JSON.parse(this.state.entityTypesSchema)
      return !deepEqual(schemas, this.props.selectedPipeline.entity_types)
    } catch (e) {
      return true
    }
  }

  render () {
    return (
      <div className='section-body'>
        <div className='section-left'>
          <EntityTypeViewer schema={this.props.selectedPipeline.entity_types} />
        </div>

        <div className='section-right'>
          <form onSubmit={this.notifyChange.bind(this)}>
            <label className='form-label'>
              <FormattedMessage
                id='entitytype.empty.message'
                defaultMessage='Paste Entity Type definitions'
              />
            </label>
            <FormattedMessage id='entityTypeSchema.placeholder' defaultMessage='Enter your schemas'>
              {message => (
                <textarea
                  className='monospace'
                  value={this.state.entityTypesSchema}
                  onChange={this.onSchemaTextChanged.bind(this)}
                  placeholder={message}
                  rows='10'
                />
              )}
            </FormattedMessage>

            { this.state.error &&
              <div className='hint'>
                <h4>
                  <FormattedMessage
                    id='entitytype.invalid.message'
                    defaultMessage='You have provided invalid AVRO schemas.'
                  />
                </h4>
                <br />
                { this.state.error }
              </div>
            }

            <button type='submit' className='btn btn-d btn-primary mt-3' disabled={!this.hasChanged()}>
              <span className='details-title'>
                <FormattedMessage
                  id='entitytype.button.ok'
                  defaultMessage='Add to pipeline'
                />
              </span>
            </button>
          </form>
        </div>
      </div>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  selectedPipeline: pipelines.selectedPipeline
})

export default connect(mapStateToProps, { updatePipeline })(EntityTypes)
