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
    selector: '.website_event_track',
    /*xmlDependencies: ['/website_event_track_uclv/static/src/xml/website_event_track_uclv_share_templates.xml'],*/
    events: {
        'click .add_author': '_onAddAuthorClick',
        'submit .js_wforum_submit_form:has(:not(.karma_required).o_wforum_submit_post)': '_onSubmitForm',
    },

    /**
     * @override
     */
    start: function () {
        var self = this;

        /*this.lastsearch = [];*/

        // float-left class messes up the post layout OPW 769721
        /*$('span[data-oe-model="forum.post"][data-oe-field="content"]').find('img.float-left').removeClass('float-left');*/

        // welcome message action button
        /*var forumLogin = _.string.sprintf('%s/web?redirect=%s',
            window.location.origin,
            escape(window.location.href)
        );*/
        /*$('.forum_register_url').attr('href', forumLogin);*/

        // Initialize forum's tooltips
        /*this.$('[data-toggle="tooltip"]').tooltip({delay: 0});
        this.$('[data-toggle="popover"]').popover({offset: 8});*/

        /*$('input.js_select2').select2({
            tags: true,
            tokenSeparators: [',', ' ', '_'],
            maximumInputLength: 35,
            minimumInputLength: 2,
            maximumSelectionSize: 5,
            lastsearch: [],
            createSearchChoice: function (term) {
                if (_.filter(self.lastsearch, function (s) {
                    return s.text.localeCompare(term) === 0;
                }).length === 0) {
                    //check Karma
                    if (parseInt($('#karma').val()) >= parseInt($('#karma_edit_retag').val())) {
                        return {
                            id: '_' + $.trim(term),
                            text: $.trim(term) + ' *',
                            isNew: true,
                        };
                    }
                }
            },
            formatResult: function (term) {
                if (term.isNew) {
                    return '<span class="badge badge-primary">New</span> ' + _.escape(term.text);
                } else {
                    return _.escape(term.text);
                }
            },
            ajax: {
                url: '/forum/get_tags',
                dataType: 'json',
                data: function (term) {
                    return {
                        query: term,
                        limit: 50,
                    };
                },
                results: function (data) {
                    var ret = [];
                    _.each(data, function (x) {
                        ret.push({
                            id: x.id,
                            text: x.name,
                            isNew: false,
                        });
                    });
                    self.lastsearch = ret;
                    return {results: ret};
                }
            },
            // Take default tags from the input value
            initSelection: function (element, callback) {
                var data = [];
                _.each(element.data('init-value'), function (x) {
                    data.push({id: x.id, text: x.name, isNew: false});
                });
                element.val('');
                callback(data);
            },
        });*/

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
            };
            
            wysiwygLoader.load(self, $textarea[0], options).then(wysiwyg => {
                $form.find('.note-editable').find('img.float-left').removeClass('float-left');
                $form.on('click', 'button .a-submit', () => {
                    wysiwyg.save();
                });
            });
        });

                
        return this._super.apply(this, arguments);
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
        let validForm = true;

        let $form = $(ev.currentTarget);
        let $title = $form.find('input[name=post_name]');
        let $textarea = $form.find('textarea[name=content]');
        // It's not really in the textarea that the user write at first
        let textareaContent = $form.find('.o_wysiwyg_wrapper .note-editable.panel-body').text().trim();

        if ($title.length && $title[0].required) {
            if ($title.val()) {
                $title.removeClass('is-invalid');
            } else {
                $title.addClass('is-invalid');
                validForm = false;
            }
        }

        // Because the textarea is hidden, we add the red or green border to its container
        if ($textarea[0] && $textarea[0].required) {
            let $textareaContainer = $form.find('.o_wysiwyg_wrapper .note-editor.panel.panel-default');
            if (!textareaContent.length) {
                $textareaContainer.addClass('border border-danger rounded-top');
                validForm = false;
            } else {
                $textareaContainer.removeClass('border border-danger rounded-top');
            }
        }

        if (validForm) {
            // Stores social share data to display modal on next page.
            if ($form.has('.oe_social_share_call').length) {
                sessionStorage.setItem('social_share', JSON.stringify({
                    targetType: $(ev.currentTarget).find('.o_wforum_submit_post').data('social-target-type'),
                }));
            }
        } else {
            ev.preventDefault();
            setTimeout(function() {
                var $buttons = $(ev.currentTarget).find('button[type="submit"], a.a-submit');
                _.each($buttons, function (btn) {
                    let $btn = $(btn);
                    $btn.find('i').remove();
                    $btn.prop('disabled', false);
                });
            }, 0);
        }
    }, 
    _onAddAuthorClick: function (ev) {
        alert('hi')
        ev.preventDefault();
    },    
});



});
