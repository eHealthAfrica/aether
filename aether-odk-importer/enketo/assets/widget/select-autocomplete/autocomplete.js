'use strict';

var $ = require( 'jquery' );
var Widget = require( '../../js/Widget' );
var pluginName = 'autocomplete';
var sadExcuseForABrowser = !( 'list' in document.createElement( 'input' ) &&
    'options' in document.createElement( 'datalist' ) &&
    typeof window.HTMLDataListElement !== 'undefined' );

require( './jquery.relevant-dropdown' );

/**
 *  Autocomplete select1 picker for modern browsers.
 * 
 * @constructor
 * @param {Element} element [description]
 * @param {(boolean|{touch: boolean, btnStyle: string, noneSelectedText: string, maxlength:number})} options options
 * @param {*=} e     event
 */

function Selectpicker( element, options, e ) {
    this.namespace = pluginName;
    Widget.call( this, element, options );
    if ( e ) {
        e.stopPropagation();
        e.preventDefault();
    }
    this._init();
}

Selectpicker.prototype = Object.create( Widget.prototype );

Selectpicker.prototype.constructor = Selectpicker;

Selectpicker.prototype._init = function() {
    var $input = $( this.element );
    var listId = $input.attr( 'list' );

    this.props = this._getProps();
    this.$options = $input.closest( '.question' ).find( 'datalist#' + listId + ' > option' );

    // This value -> data-value change is not slow, so no need to move to enketo-xslt as that would 
    // increase itemset complexity even further.
    this.$options.each( function( index, item ) {
        var value = item.getAttribute( 'value' );
        /**
         * We're changing the original datalist here, so have to make sure we don't do anything
         * if dataset.value is already populated.
         * 
         * However, for some reason !item.dataset.value is failing in Safari, which as a result sets all dataset.value attributes to "null" 
         * To workaround this, we check for the value attribute instead.
         */
        if ( !item.classList.contains( 'itemset-template' ) && value !== undefined && value !== null ) {
            item.dataset.value = value;
            item.removeAttribute( 'value' );
        }
    } );

    this.$fakeInput = $( '<input type="text" class="ignore widget autocomplete" list="' + listId + '" />' );
    if ( this.props.readonly ) {
        this.$fakeInput.attr( 'readonly', 'readonly' );
    }
    if ( this.props.disabled ) {
        this.$fakeInput.attr( 'disabled', 'disabled' );
    }

    $input.hide().after( this.$fakeInput );

    if ( sadExcuseForABrowser ) {
        console.debug( 'Polyfill required' );
        this.$fakeInput.relevantDropdown();
    }

    this._setFakeInputListener();
    this._setFocusListener();
    this._showCurrentLabel(); // after setting fakeInputListener!
};

Selectpicker.prototype._getProps = function() {
    return {
        readonly: this.element.readOnly,
        disabled: this.element.disabled
    };
};

Selectpicker.prototype._showCurrentLabel = function() {
    var value = this.element.value;
    var label = this._findLabel( value );

    this.$fakeInput.val( label );

    // If a corresponding label cannot be found the value is invalid,
    // and should be cleared. For this we trigger an 'input' event.
    if ( value && !label ) {
        this.$fakeInput.trigger( 'input' );
    }
};

Selectpicker.prototype._setFakeInputListener = function() {
    var that = this;

    this.$fakeInput.on( 'input.' + this.namespace, function( e ) {
        var input = e.target;
        var label = input.value.trim();
        var value = that._findValue( label ) || '';
        if ( that.element.value !== value ) {
            $( that.element ).val( value ).trigger( 'change' );
        }
        $( input ).toggleClass( 'notfound', label && !value );
    } );
};

Selectpicker.prototype._findValue = function( label ) {
    var value = '';

    if ( !label ) {
        return '';
    }

    this.$options.each( function( i, option ) {
        if ( option.innerText === label ) {
            value = option.getAttribute( 'data-value' );
            return false;
        }
    } );

    return value;
};

Selectpicker.prototype._findLabel = function( value ) {
    var label = '';

    if ( !value ) {
        return '';
    }

    this.$options.each( function( i, option ) {
        if ( option.dataset.value === value ) {
            label = option.value;
            return false;
        }
    } );
    return label;
};

Selectpicker.prototype._setFocusListener = function() {
    var _this = this;

    // Handle widget focus
    this.$fakeInput.on( 'focus', function() {
        $( _this.element ).trigger( 'fakefocus' );
        return true;
    } );

    // Handle original input focus
    $( this.element ).on( 'applyfocus', function() {
        $( _this.$fakeInput ).focus();
    } );
};

// override super method
Selectpicker.prototype.disable = function() {
    this.$fakeInput.find( 'li' ).addClass( 'disabled' );
};

// override super method
Selectpicker.prototype.enable = function() {
    this.$fakeInput.find( 'li' ).removeClass( 'disabled' );
};

// override super method
Selectpicker.prototype.update = function() {
    /*
     * There are 3 scenarios for which method is called:
     * 1. The options change (dynamic itemset)
     * 2. The language changed. (just this._showCurrentLabel() would be more efficient)
     * 3. The value of the underlying original input changed due a calculation. (same as #2?)
     * 
     * For now we just dumbly reinstantiate it (including the polyfill).
     */
    $( this.element ).siblings( '.widget' ).remove();
    this._init();
};

/**
 * Register jQuery plugin
 * 
 * @param {*} option options
 * @param {*=} event       [description]
 */
$.fn[ pluginName ] = function( options, event ) {

    options = options || {};

    return this.each( function() {

        var $this = $( this ),
            data = $this.data( pluginName );

        //only instantiate if options is an object
        if ( !data && typeof options === 'object' ) {
            $this.data( pluginName, ( data = new Selectpicker( this, options, event ) ) );
        } else if ( data && typeof options === 'string' ) {
            data[ options ]( this );
        }
    } );
};


module.exports = {
    'name': pluginName,
    'list': true,
    'selector': 'input[list]'
};
