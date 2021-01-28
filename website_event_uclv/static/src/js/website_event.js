odoo.define('website_event.registration_form.instance', function (require) {
'use strict';

require('web_editor.ready');
var EventRegistrationForm = require('website_event.website_event');

var $form = $('#registration_form');
if (!$form.length) {
    return null;
}

var instance = new EventRegistrationForm();
return instance.appendTo($form).then(function () {
    return instance;
});
});

//==============================================================================

odoo.define('website_event.website_event', function (require) {

var ajax = require('web.ajax');
var Widget = require('web.Widget');

// Catch registration form event, because of JS for attendee details
var EventRegistrationForm = Widget.extend({
    start: function () {
        var self = this;
        var res = this._super.apply(this.arguments).then(function () {
            $('#registration_form .a-submit')
                .off('click')
                .removeClass('a-submit')
                .click(function (ev) {
                    /*$(this).attr('disabled', true);*/
                    self.on_click(ev);
                });
        });
        return res;
    },
    on_click: function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        var $form = $(ev.currentTarget).closest('form');
        var post = {};
        $('#registration_form select').each(function () {
            post[$(this).attr('name')] = $(this).val();
        });
        var tickets_ordered = _.some(_.map(post, function (value, key) { return parseInt(value); }));
        if (!tickets_ordered) {

            /*alert("Please select at least one ticket.")
            return $('#registration_form').after(
                '<div class="alert alert-info">Please select at least one ticket.</div>'
            );*/
            if (document.getElementById('register_error_modal'))
            {
                $('#register_error_modal').modal();
                return;
            }
            else
            {
                var html = '<div id="register_error_modal" class="modal fade" role="dialog"> <div class="modal-dialog modal-danger"> <div class="modal-content"> <div class="modal-header"> <button type="button" class="close" data-dismiss="modal" aria-label="Cerrar"><span aria-hidden="true">&times;</span></button> <h5 class="modal-title">Registro</h5> </div> <div class="modal-body"><div class="row"><div class="col-xs-1"><span class="fa fa-warning text-warning fa-4x fa-fw"></span></div><div class="col-xs-11"><span class="h6">Debe seleccionar alguna cantidad de al menos un ticket para continuar el registro</span></div></div></div> <div class="modal-footer"> <button class="btn btn-default pull-right"  data-dismiss="modal">OK</button></div> </div> </div> </div>';
                $('body').after(html);
                $('#register_error_modal').modal();
                return;
            }
        } else {
            return ajax.jsonRpc($form.attr('action'), 'call', post).then(function (modal) {
                var $modal = $(modal);
                $modal.find('.modal-body > div').removeClass('container'); // retrocompatibility - REMOVE ME in master / saas-19
                $modal.modal();
                $modal.on('click', '.js_goto_event', function () {
                    $modal.modal('hide');
                });
            });
        }
    },
});

return EventRegistrationForm;
});
