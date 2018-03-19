import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

class AppLayout extends Component { 
    render() {
        return(
            <div>This is a React App</div>
        );
    }
}

const mapStateToProps = ({ }) => ({ });

export default connect(mapStateToProps, {})(AppLayout);