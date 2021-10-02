odoo.define('website_event_track_uclv.portal_event_review', function (require) {
'use strict';

const dom = require('web.dom');
const publicWidget = require('web.public.widget');

publicWidget.registry.portalEventReview = publicWidget.Widget.extend({
    selector: '.portal_event_review',
    /**
     * @override
     */
    
    start: function () {        
        $('.js_tweet, .js_comment').sharetrack({});
        return this._super.apply(this, arguments);
    },   
});
});
