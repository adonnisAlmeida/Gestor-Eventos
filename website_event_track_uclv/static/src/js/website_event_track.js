odoo.define('website_event_track_uclv.website_event_track', function (require) {
'use strict';

const dom = require('web.dom');
var core = require('web.core');
var weDefaultOptions = require('web_editor.wysiwyg.default_options');
var wysiwygLoader = require('web_editor.loader');
var publicWidget = require('web.public.widget');
var session = require('web.session');
var qweb = core.qweb;


var _t = core._t;


publicWidget.registry.websiteEventTrack = publicWidget.Widget.extend({
    selector: '.website_event_track_proposal',
    events: {
        'click .js_add_author': '_onAddAuthorClick',
        'click .js_add_author_modal_cancel': '_onAddAuthorCancelClick',
        'click .js_add_author_modal_save': '_onAddAuthorSaveClick',
        'click .js_edit_author_modal_cancel': '_onEditAuthorCancelClick',
        'click .js_edit_author_modal_save': '_onEditAuthorSaveClick',
        'click .js_delete_author': '_onDeleteAuthorClick',
        'click .js_edit_author': '_onEditAuthorClick',
        'submit': '_onSubmitForm',
    },
    renderAuthors: function()
    {
        this.$('#authors_list').html('');
        for (var i=0; i<this.authors_list.length; i++)
        {
            var au = this.authors_list[i];
            if (au.author_id == 0)
            {
                this.$('#authors_list').append(`
                    <li data-author-id="0">
                        <div class="input-group ui-sortable-handle">
                            <div class="input-group-prepend ui-sortable-handle">
                                <span class="input-group-text fa fa-bars" role="img" aria-label="Drag to sort" title="Drag to sort"></span>
                            </div>
                            <div class="form-control d-flex flex-column" style="height: auto !important;">
                                
                                <span class="h4">`+this.current_user_name+`</span>
                                
                                <div>
                                    <span class="small fa fa-envelope mr-1 text-secondary"></span>
                                    <span class="small text-truncate">`+this.current_user_email+`</span>
                                </div>
                                <div>
                                    <span class="small fa fa-home mr-1 text-secondary"></span>
                                    <span class="text-muted small text-truncate mr-1">`+this.current_user_institution+`</span>
                                    <span>
                                        <img height="12px" src="`+this.current_user_country_image+`" alt="Flag of `+this.current_user_country_name+`" title="`+this.current_user_country_name+`"/>
                                    </span>
                                </div>                    
                            </div>
                        </div>
                    </li>`);
                   
            }
            else
            {
                this.$('#authors_list').append(`
                    <li data-author-id="`+au.author_id+`">
                        <div class="input-group ui-sortable-handle">
                            <div class="input-group-prepend ui-sortable-handle">
                                <span class="input-group-text fa fa-bars" role="img" aria-label="Drag to sort" title="Drag to sort"></span>
                            </div>
                            <div class="form-control d-flex flex-column `+(au.error?'is-invalid':'')+`" style="height: auto !important;">
                                
                                <span class="h4 text-truncate">`+au.author_name+`</span>
                                
                                <div>
                                    <span class="small fa fa-envelope mr-1 text-secondary" ></span>
                                    <span class="small text-truncate">`+au.author_email+`</span>
                                </div>
                                <div>
                                    <span class="small fa fa-home mr-1 text-secondary"></span>
                                    <span class="text-muted small text-truncate mr-1">`+au.author_institution+`</span>
                                    <span>
                                        <img height="12px" src="`+au.author_country_image+`" alt="Flag of `+au.author_country_name+`" title="`+au.author_country_name+`"/>
                                    </span>
                                </div>                    
                            </div>
                            <span class="input-group-append">
                                <button type="button" class="btn btn-primary js_edit_author fa fa-pencil-square-o" aria-label="Edit Author" title="Edit Author"></button>
                                <button type="button" class="btn btn-danger js_delete_author fa fa-trash-o" aria-label="Delete Author" title="Delete Author"></button>
                            </span>
                        </div>
                    </li>`);
            }
        }
    },    
    /**
     * @override
     */
    start: function () {
        var self = this;
        if (this.$('#authors').attr('value') == undefined)
            return;
        this.authors_list = JSON.parse(this.$('#authors').attr('value'));
        this.current_user_name = this.$('#current_user_name').attr('value');
        this.current_user_email = this.$('#current_user_email').attr('value');
        this.current_user_institution = this.$('#current_user_institution').attr('value');
        this.current_user_country_image = this.$('#current_user_country_image').attr('value');
        this.current_user_country_name = this.$('#current_user_country_name').attr('value');

        this.$('#authors_list').sortable({
            listType: 'ol',
            handle: 'div',
            items: 'li',
            toleranceElement: '> div',
            forcePlaceholderSize: true,
            opacity: 0.6,
            placeholder: 'oe_menu_placeholder',
            tolerance: 'pointer',
            attribute: 'data-author-id',
            expression: '()(.+)',
            update: function(ev, ui) 
            {                
                var ordered_ids = $('#authors_list').sortable('toArray', { attribute:"data-author-id"});
                
                var ordered = []
                for (var i=0; i < ordered_ids.length; i++)
                {
                    for(var j=0; j< self.authors_list.length;j++)
                    {
                        if(self.authors_list[j].author_id == ordered_ids[i])
                        {
                            ordered.push(self.authors_list[j]);
                            break;
                        }
                    }
                }
                self.authors_list = ordered;
                console.warn(self.authors_list)
            }
        });
        
        this.renderAuthors();       

        _.each($('textarea.o_wysiwyg_loader'), function (textarea) {
            var $textarea = $(textarea);
            var $form = $textarea.closest('form');
            var toolbar = [
                ['style', ['style']],
                ['font', ['bold', 'italic', 'underline', 'strikethrough', 'superscript', 'subscript', 'clear']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['table', ['table']],
                ['view', ['codeview', 'help']],
            ];
            
            toolbar.push(['insert', ['link', 'picture']]);
            
            toolbar.push(['history', ['undo', 'redo']]);
            
            var options = {
                height: 200,
                minHeight: 80,
                toolbar: toolbar,
                styleWithSpan: false,
                styleTags: _.without(weDefaultOptions.styleTags, 'h1', 'h2', 'h3', 'pre', 'small'),
                onPaste: function (e) {
                    var bufferText = ((e.originalEvent || e).clipboardData || window.clipboardData).getData('Text');
                    e.preventDefault();
                    document.execCommand('insertText', false, bufferText);
                }               
            };
            
            wysiwygLoader.load(self, $textarea[0], options).then(wysiwyg => {
                $form.find('.note-editable').find('img.float-left').removeClass('float-left');
                $form.on('click', 'button .a-submit', () => {
                    wysiwyg.save();
                });
            });
        });

        $("#fileuploader").uploadFile({
            url:"http://hayageek.com/examples/jquery/ajax-multiple-file-upload/upload.php",
            fileName:"myfile"
        });
             
        return this._super.apply(this, arguments);
    },
    createUUID: function()
    {
        return Math.floor(Math.random() * Date.now())
    },
    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     *
     * @override
     * @param {Event} ev
     */
    _onSubmitForm: function (ev) {
        // build authors data in JSON before sending to server
        this.$('#authors').attr('value', JSON.stringify(this.authors_list));             
    }, 
    _onAddAuthorClick: function (ev) {
        let $form = $('#add_author_form');
        $form[0].reset()
        let $inputs = $form.find('input');
        $inputs.removeClass('is-invalid');        
        $('#modal_add_author').modal("toggle");
        ev.preventDefault();
    }, 
    _onAddAuthorSaveClick: function (ev) {
        let $btn = $(ev.currentTarget);
        let validForm = true;
        let $form = $('#add_author_form');
        let $author_name = $form.find('input[name=author_name]');
        if ($author_name.length && $author_name[0].required) {
            if ($author_name.val()) {
                $author_name.removeClass('is-invalid');
            } else {
                $author_name.addClass('is-invalid');
                validForm = false;
            }
        }

        let $author_email = $form.find('input[name=author_email]');
        
        var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
        if ($author_email.length && $author_email[0].required) {
            if ($author_email.val() && emailReg.test($author_email.val())) {
                $author_email.removeClass('is-invalid');
            } else {
                $author_email.addClass('is-invalid');
                validForm = false;
            }
        }
        let $author_institution = $form.find('input[name=author_institution]');
        let $author_country_id = $form.find('select[name=author_country_id]');

        if (validForm) {
            var uid = this.createUUID(); 
            var option = $author_country_id[0].options[$author_country_id[0].selectedIndex];
            var data = {
                author_id: uid,
                author_name: $author_name.val(),
                author_email: $author_email.val(),
                author_institution: $author_institution.val(),
                author_country_name: option.text,
                author_country_image: option.getAttribute('data-url'),
                author_country_id: $author_country_id.val()
            }            
            this.authors_list.push(data);
            this.renderAuthors();
            $('#modal_add_author').modal("toggle");
        }       
        ev.preventDefault();
    },
    _onEditAuthorSaveClick: function (ev) {
        let $btn = $(ev.currentTarget);
        let validForm = true;
        let $form = $('#edit_author_form');
        let $author_id = $form.find('input[name=author_id]');
        let $author_name = $form.find('input[name=author_name]');
        if ($author_name.length && $author_name[0].required) {
            if ($author_name.val()) {
                $author_name.removeClass('is-invalid');
            } else {
                $author_name.addClass('is-invalid');
                validForm = false;
            }
        }

        let $author_email = $form.find('input[name=author_email]');
        
        var emailReg = /^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
        if ($author_email.length && $author_email[0].required) {
            if ($author_email.val() && emailReg.test($author_email.val())) {
                $author_email.removeClass('is-invalid');
            } else {
                $author_email.addClass('is-invalid');
                validForm = false;
            }
        }
        let $author_institution = $form.find('input[name=author_institution]');

        let $author_country_id = $form.find('select[name=author_country_id]');
        
        if (validForm) {            
            var option = $author_country_id[0].options[$author_country_id[0].selectedIndex];
            var data = {
                author_id: $author_id.val(),
                author_name: $author_name.val(),
                author_email: $author_email.val(),
                author_institution: $author_institution.val(),
                author_country_name: option.text,
                author_country_image: option.getAttribute('data-url'),
                author_country_id: $author_country_id.val()
            }
            for (var i=0; i<this.authors_list.length;i++)
            {
                if(this.authors_list[i].author_id == data.author_id)
                {
                    this.authors_list[i] = data;
                    break;
                }
            }
            this.renderAuthors();
            $('#modal_edit_author').modal("toggle");
        }       
        ev.preventDefault();
    },
    _onDeleteAuthorClick: function (ev) {        
        var $author = $(ev.currentTarget).closest('[data-author-id]');
        var uid = $author.attr('data-author-id');
        var copy = []
        for (var i=0; i<this.authors_list.length;i++)
        {
            if(this.authors_list[i].author_id != uid)
            {
                copy.push(this.authors_list[i]);                
            }
        }
        this.authors_list = copy;
        this.renderAuthors();
    },
    _onEditAuthorClick: function (ev) {
        var $author = $(ev.currentTarget).closest('[data-author-id]');
        var uid = $author.attr('data-author-id');
        var item = {};
        for (var i=0; i<this.authors_list.length;i++)
        {
            if(this.authors_list[i].author_id == uid)
            {
                item = this.authors_list[i];
                break;
            }
        }
        let $form = $('#edit_author_form');
        $form[0].reset()
        let $inputs = $form.find('input');
        $inputs.removeClass('is-invalid');

        $form.find('input[name=author_id]').attr('value', item.author_id);
        $form.find('input[name=author_name]').attr('value', item.author_name);
        $form.find('input[name=author_email]').attr('value', item.author_email);
        $form.find('input[name=author_institution]').attr('value', item.author_institution);
        $form.find('select[name=author_country_id]').val(item.author_country_id).change();
        
        if (item.error && item.error.author_name)
        {
            $form.find('input[name=author_name]').addClass('is-invalid');
            $form.find('div[name=author_name_error_feedback]').html(item.error.author_name);
        }
        if (item.error && item.error.author_email)
        {
            $form.find('input[name=author_email]').addClass('is-invalid');
            $form.find('div[name=author_email_error_feedback]').html(item.error.author_email);
        }

        $('#modal_edit_author').modal("toggle");
        ev.preventDefault();
    },
    _onAddAuthorCancelClick: function (ev) {        
        $('#modal_add_author').modal("toggle");
        ev.preventDefault();        
    },
    _onEditAuthorCancelClick: function (ev) {        
        $('#modal_edit_author').modal("toggle");
        ev.preventDefault();        
    },
});



});
