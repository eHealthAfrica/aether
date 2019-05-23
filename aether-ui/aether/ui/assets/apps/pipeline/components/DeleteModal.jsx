import React, { Component } from 'react'
import { FormattedMessage } from 'react-intl'
import { Modal } from '../../components'

class DeleteModal extends Component {
  constructor (props) {
    super(props)
    this.state = {
      schemas: false,
      entities: false,
      submissions: false
    }
  }

  render () {
    const header = (
      <span>
        <FormattedMessage
          id='delete.modal.header'
          defaultMessage={this.props.header}
        />
        <span className='bold'>{this.props.obj.name}?</span>
      </span>
    )

    const buttons = (
      <div>
        <button
          data-qa='delete.modal.button.cancel'
          className='btn btn-w'
          onClick={this.props.onClose}>
          <FormattedMessage
            id='delete.modal.button.cancel'
            defaultMessage='Cancel'
          />
        </button>

        <button className='btn btn-w btn-primary' onClick={() => this.props.onDelete(this.state)}>
          <FormattedMessage
            id='delete.modal.button.delete'
            defaultMessage='Delete'
          />
        </button>
      </div>
    )

    return (
      <Modal header={header} buttons={buttons}>
        <label className='title-medium mt-4'>
          <FormattedMessage
            id='delete.modal.message-2'
            defaultMessage='Would you also like to delete any of the following?'
          />
        </label>
        {
          this.props.objectType === 'pipeline' &&
          <div className='check-default ml-4'>
            <input type='checkbox' id='check1' checked={this.state.submissions}
              onChange={(e) => {
                this.setState({
                  ...this.state, submissions: e.target.checked
                })
              }}
            />
            <label for='check1'>
              <FormattedMessage
                id='delete.modal.all.submissions-0'
                defaultMessage='Data'
              />
              <span className='bold mx-2'>
                <FormattedMessage
                  id='delete.modal.all.submissions-1'
                  defaultMessage='submitted to'
                />
              </span>
              <FormattedMessage
                id='delete.modal.all.submissions-2'
                defaultMessage='this pipeline (Submissions)'
              />
            </label>
          </div>
        }
        <div className='check-default ml-4'>
          <input type='checkbox' id='check2' checked={this.state.schemas}
            onChange={(e) => {
              this.setState({
                ...this.state,
                schemas: e.target.checked,
                entities: e.target.checked
              })
            }}
          />
          <label for='check2'>
            <FormattedMessage
              id='delete.modal.all.entity-types-0'
              defaultMessage='Entity Types (Schemas)'
            />
          </label>
        </div>
        <div className='check-default ml-4 check-indent'>
          <input type='checkbox' id='check3' checked={this.state.entities}
            onChange={(e) => {
              if (!e.target.checked) {
                this.setState({
                  ...this.state,
                  entities: e.target.checked,
                  schemas: e.target.checked
                })
              } else {
                this.setState({
                  ...this.state, entities: e.target.checked
                })
              }
            }}
          />
          <label for='check3'>
            <FormattedMessage
              id='delete.modal.all.data-0'
              defaultMessage='Data'
            />
            <span className='bold mx-2'>
              <FormattedMessage
                id='delete.modal.all.data-1'
                defaultMessage='created by'
              />
            </span>
            <FormattedMessage
              id='delete.modal.all.data-2'
              defaultMessage={`this ${this.props.objectType} (Entities)`}
            />
          </label>
        </div>
      </Modal>
    )
  }
}

export default DeleteModal
