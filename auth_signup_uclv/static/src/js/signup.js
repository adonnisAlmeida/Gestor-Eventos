 
odoo.define('auth.signup.uclv', function (require) {
'use strict';

    var publicWidget = require('web.public.widget');
    publicWidget.registry.SignUpForm = publicWidget.Widget.extend({
        selector: '.oe_signup_form',
        events: {
            'change select[name="country_id"]': '_onCountryChange',
            'submit': '_onSubmit',
        },

        /**
         * @override
         */
        start: function () {
            var def = this._super.apply(this, arguments);

            this.$state = this.$('select[name="state_id"]');
            this.$stateOptions = this.$state.filter(':enabled').find('option:not(:first)');
            this._adaptAddressForm();

            return def;
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _adaptAddressForm: function () {
            var $country = this.$('select[name="country_id"]');
            var countryID = ($country.val() || 0);
            this.$stateOptions.detach();
            var $displayedState = this.$stateOptions.filter('[data-country_id=' + countryID + ']');
            var nb = $displayedState.appendTo(this.$state).show().length;
            this.$state.parent().toggle(nb >= 1);
            this.$state.prop('required',(nb >= 1));
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------

        /**
         * @private
         */
        _onCountryChange: function () {
            this._adaptAddressForm();
        },
        _onSubmit: function () {
            var $btn = this.$('.oe_login_buttons > button[type="submit"]');
            $btn.attr('disabled', 'disabled');
            $btn.prepend('<i class="fa fa-refresh fa-spin"/> ');
        },
    });
});