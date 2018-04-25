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
    return JSON.stringify(props.selectedPipeline.entity_types, 0, 2)
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
      // generate sample output with new enity types (TO BE REMOVED!!!)
      const output = schemas.map(et => avro.parse(et).random())

      this.props.updatePipeline({ entity_types: schemas, output })
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
            { this.state.error &&
              <div className='hint error-message'>
                <h4 className='hint-title'>
                  <FormattedMessage
                    id='entitytype.invalid.message'
                    defaultMessage='You have provided invalid AVRO schemas.'
                  />
                </h4>
                { this.state.error }
              </div>
            }

            <FormattedMessage id='entityTypeSchema.placeholder' defaultMessage='Enter your schemas'>
              {message => (
                <textarea
                  className='input-d monospace'
                  value={this.state.entityTypesSchema}
                  onChange={this.onSchemaTextChanged.bind(this)}
                  placeholder={message}
                  rows='10'
                />
              )}
            </FormattedMessage>

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
