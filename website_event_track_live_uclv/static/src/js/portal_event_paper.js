odoo.define('website_event_track_live_uclv.portal_event_paper', function (require) {
'use strict';

const dom = require('web.dom');
const publicWidget = require('web.public.widget');
publicWidget.registry.portalEventTrack = publicWidget.Widget.extend({
    selector: '.portal_event_paper',
    /**
     * @override
     */
    
    start: function () {        
        $('.js_tweet, .js_comment').sharetrack({});
        var csrf_token = $('#csrf_token').val()
        $("#fileuploader").uploadFile({
            url:"#",
            fileName:"file",
            showFileSize: true,
            showFileCounter: false,
            maxFileSize: 20*1024*1024,
            showDone: true,
            showStatusAfterSuccess: true,
            showProgress: true,
            formData: {"csrf_token": csrf_token},
            dragDropStr: "<b>&nbsp;&nbsp;Drag and drop files here</b>",
            uploadStr: "Select a file",
            abortStr: "Abort",
            cancelStr: "Cancel",
            doneStr: "Done",
            multiDragErrorStr: "Multiple File Drag & Drop is not allowed.",
            extErrorStr: "is not allowed. Allowed extensions: ",
            duplicateErrorStr: "is not allowed. File already exists.",
            sizeErrorStr: "is not allowed. Allowed Max size: ",
            uploadErrorStr: "Upload is not allowed",
            maxFileCountErrorStr: " is not allowed. Maximum allowed files are:",           
        });
        $("#videouploader").uploadFile({
            url:"#",
            fileName:"video",
            showFileSize: true,
            showFileCounter: false,
            maxFileSize: 300*1024*1024,
            showDone: true,
            showStatusAfterSuccess: false,
            showProgress: true,
            formData: {"csrf_token": csrf_token},
            acceptFiles:'video/*,audio/*',
            dragDropStr: "<b>&nbsp;&nbsp;Drag and drop video files here</b>",
            uploadStr: "Select a video file",
            abortStr: "Abort",
            cancelStr: "Cancel",
            doneStr: "Done",
            multiDragErrorStr: "Multiple File Drag & Drop is not allowed.",
            extErrorStr: "is not allowed. Allowed extensions: ",
            duplicateErrorStr: "is not allowed. File already exists.",
            sizeErrorStr: "is not allowed. Allowed Max size: ",
            uploadErrorStr: "Upload is not allowed",
            maxFileCountErrorStr: " is not allowed. Maximum allowed files are:",
            onSuccess:function(files,data,xhr,pd)
            {
                //files: list of files
                //data: response from server
                //xhr : jquer xhr object
                
                $('#videoplayer').remove();
                $('#videoencoder').removeClass('d-none');
                
            }
        });
        $(".ajax-file-upload").addClass('btn btn-primary');        
        return this._super.apply(this, arguments);
    },   
});
});
