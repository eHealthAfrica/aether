import React, { Component } from 'react'
import { Modal } from '../../components'
import { connect } from 'react-redux'
import { FormattedMessage } from 'react-intl'

class DeleteStatus extends Component {
  constructor (props) {
    super(props)
    this.state = {
    }
  }

  componentDidUpdate () {
    if (this.props.error || (this.props.deleteStatus &&
      this.props.deleteStatus.not_published)) {
      this.props.toggle()
    }
  }

  render () {
    if (!this.props.showModal) {
      return null
    }

    const header = (
      <span>
        <FormattedMessage
          id='delete.progress.modal.header'
          defaultMessage={this.props.header}
        />
      </span>
    )

    const buttons = (
      <div>
        { this.props.deleteStatus &&
          <button
            className='btn btn-w'
            onClick={() => { this.props.toggle() }}>
            <FormattedMessage
              id='delete.progress.modal.ok'
              defaultMessage='Ok'
            />
          </button>
        }
      </div>
    )

    return (
      <Modal header={header} buttons={buttons}>
        {
          !this.props.deleteStatus && (
            <label className='title-medium mt-4'>
              <FormattedMessage
                id='delete.modal.status.head-1'
                defaultMessage='Deleting kernel artefacts...'
              />
              <i className='ml-5 fa fa-cog fa-spin' />
            </label>
          )
        }

        {
          this.props.deleteOptions.entities && this.props.deleteStatus &&
          this.props.deleteStatus.hasOwnProperty('entities') && (
            <label className='form-label'>
              <FormattedMessage
                id='delete.modal.entities.status.done'
                defaultMessage={`Deleted ${this.props.deleteStatus.entities} entities`}
              />
            </label>
          )
        }

        {
          this.props.deleteOptions.schemas && this.props.deleteStatus &&
          this.props.deleteStatus.schemas && (
            <div>
              <label className='form-label'>
                <FormattedMessage
                  id='delete.modal.entity.types.status'
                  defaultMessage='Entity types:'
                />
              </label>
              {
                Object.keys(this.props.deleteStatus.schemas).map(schema => (
                  <div key={schema}>
                    <label>
                      { `${schema} : ${this.props.deleteStatus.schemas[schema].is_deleted ? 'Deleted' : 'Not deleted, used by other mappings'}` }
                    </label>
                  </div>
                ))
              }
              {
                Object.keys(this.props.deleteStatus.schemas).length === 0 &&
                <label>
                  <FormattedMessage
                    id='delete.modal.entity.types.empty'
                    defaultMessage='No entity types to delete'
                  />
                </label>
              }
            </div>
          )
        }

        {
          this.props.deleteOptions.submissions && this.props.deleteStatus &&
          this.props.deleteStatus.hasOwnProperty('submissions') && (
            <label className='form-label'>
              <FormattedMessage
                id='delete.modal.submissions.status.done'
                defaultMessage={`Deleted ${this.props.deleteStatus.submissions} submissions`}
              />
            </label>
          )
        }
      </Modal>
    )
  }
}

const mapStateToProps = ({ pipelines }) => ({
  error: pipelines.error,
  deleteStatus: pipelines.deleteStatus
})

export default connect(mapStateToProps, {})(DeleteStatus)
