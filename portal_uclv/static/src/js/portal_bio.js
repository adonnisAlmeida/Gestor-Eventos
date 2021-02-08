odoo.define('portal_uclv.portal_bio', function (require) {
    'use strict';

    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var weDefaultOptions = require('web_editor.wysiwyg.default_options');
    var wysiwygLoader = require('web_editor.loader');
    var _t = core._t;

    publicWidget.registry.PortalBio = publicWidget.Widget.extend({
        selector: '#portal_bio',
        
        init: function () {
            this._super.apply(this, arguments);
        },

        start: function () {
            var self = this;
            _.each($('textarea.o_wysiwyg_loader'), function (textarea) {
                var $textarea = $(textarea);                
                var $form = $textarea.closest('form');                
                var toolbar = [
                    ['style', ['style']],
                    ['font', ['bold', 'italic', 'underline', 'strikethrough', 'superscript', 'subscript', 'clear']],
                    ['para', ['paragraph']],
                    /*['table', ['table']],*/
                    ['view', ['codeview', 'help']],
                ];
                
                toolbar.push(['history', ['undo', 'redo']]);
    
                var options = {
                    height: 200,
                    minHeight: 80,
                    toolbar: toolbar,
                    styleWithSpan: false,
                    spellCheck: false,
                    styleTags: _.without(weDefaultOptions.styleTags, 'h1', 'h2', 'h3', 'pre', 'small'),
                    onPaste: function (e) {
                        var bufferText = ((e.originalEvent || e).clipboardData || window.clipboardData).getData('Text');
                        e.preventDefault();
                        document.execCommand('insertText', false, bufferText);
                    }                     
                };
                
                options.plugins = {
                    LinkPlugin: false,
                    MediaPlugin: false,
                };
                
                wysiwygLoader.load(self, $textarea[0], options).then(wysiwyg => {                    
                    $form.on('click', 'button .a-submit', () => {
                        wysiwyg.save();
                    });
                });
            });
        },        
    })
});
