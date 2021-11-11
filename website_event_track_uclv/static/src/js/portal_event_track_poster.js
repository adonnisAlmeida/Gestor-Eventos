odoo.define('website_event_track_uclv.track_poster', function (require) {
    'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');    
    var _t = core._t;

    publicWidget.registry.EventTrackPoster = publicWidget.Widget.extend({
        selector: '#track_poster',
        read_events: {
            'click .track_poster_edit': '_onEditPosterClick',
            'change .track_poster_upload': '_onPosterUploadChange',
            'click .track_poster_clear': '_onClearPosterClick',
        },

        init: function () {
            this._super.apply(this, arguments);
        },

        start: function () {
            var self = this;
            
        },

        _onEditPosterClick: function (ev) {
            ev.preventDefault();
            $(ev.currentTarget).closest('form').find('.track_poster_upload').trigger('click');
        },

        _onPosterUploadChange: function (ev) {
            if (!ev.currentTarget.files.length) {
                return;
            }
            var $form = $(ev.currentTarget).closest('form');
            var reader = new window.FileReader();
            reader.readAsDataURL(ev.currentTarget.files[0]);
            reader.onload = function (ev) {
                $form.find('.track_poster_img').attr('src', ev.target.result);
                $form.find('.track_poster_img').attr('style', 'border-radius: 5%; width: 256px;')
            };
            $form.find('#track_clear_poster').remove();
        },

        _onClearPosterClick: function (ev) {
            var $form = $(ev.currentTarget).closest('form');
            $form.find('.track_poster_img').attr('src', '/web/static/src/img/placeholder.png');
            $form.find('.track_poster_img').attr('style', 'border-radius: 5`%; width: 256px;')
            $form.append($('<input/>', {
                name: 'clear_poster',
                id: 'track_clear_poster',
                type: 'hidden',
            }));
        },
    })
});
