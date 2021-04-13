# -*- coding: utf-8 -*-
import odoo
from odoo import fields, models, api, exceptions, sql_db
from odoo.tools import config 
import base64
from random import randint
import uuid


class Importer(models.TransientModel):
    _name = 'v13.importer'

    def _get_databases(self):
        result = []
        username = config['db_user']

        self.env.cr.execute("select datname from pg_database, pg_user where pg_database.datdba=pg_user.usesysid and pg_user.usename='%s';" %(username))
        data = self.env.cr.fetchall()

        for d in data:
            if str(d[0]) != self.env.cr.dbname:
                result.append((d[0], d[0]))
        result.sort()
        return result

    @api.onchange('src_db')
    def onchange_src_db(self):
        for item in self:
            if item.src_db:
                item.src_filestore = config.filestore(item.src_db)

    src_db = fields.Selection(_get_databases, 'Source Database', required=True, size=64)
    src_filestore = fields.Char('Source Filestore', required=True, size=1024)
    
    state = fields.Selection([('import', 'Import'), ('done', 'Done')], string="State", default='import')

    def case_import(self):
        cr = sql_db.db_connect(self.src_db).cursor()
        
        # res_country
        res_country = {}
        """
            id integer NOT NULL DEFAULT nextval('res_country_id_seq'::regclass),
            name character varying NOT NULL, -- Country Name
            code character varying(2), -- Country Code            
        """
        cr.execute("""select id, name, code from res_country where true;""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['res.country'].with_context(lang='en_US').search(['|',('name' , '=', d[1]),('code' , '=', d[2])])
            if exist:
                res_country.update({ d[0]: exist[0].id})
            else:
                created = self.env['res.country'].create({
                    'name': d[1],
                    'code': d[2]
                })
                res_country.update({ d[0]: created.id})
        country_cu = self.env['res.country'].with_context(lang='en_US').search([('name' , '=', 'Cuba')])
        
        # res_country_state
        res_country_state = {}
        """
            id integer NOT NULL DEFAULT nextval('res_country_state_id_seq'::regclass),
            country_id integer NOT NULL, -- Country
            name character varying NOT NULL, -- State Name
            code character varying NOT NULL, -- State Code           
        """
        cr.execute("""select id, country_id, name, code from res_country_state where true;""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['res.country.state'].with_context(lang='en_US').search([('country_id', '=', res_country[d[1]]), '|', ('name' , '=', d[2]), ('code', '=', d[3])])
            if exist:
                res_country_state.update({ d[0]: exist[0].id})
            else:
                created = self.env['res.country.state'].create({
                    'country_id': res_country[d[1]],
                    'name': d[2],
                    'code': d[3]
                })
                res_country_state.update({ d[0]: created.id})

        # res_partner_title
        res_partner_title = {}
        """
            id integer NOT NULL DEFAULT nextval('res_partner_title_id_seq'::regclass),
            name character varying NOT NULL, -- Title
            shortcut character varying, -- Abbreviation
        """
        cr.execute("""select id, name, shortcut from res_partner_title where true;""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['res.partner.title'].search([('name' , '=', d[1]), ('shortcut', '=', d[2])])
            if exist:
                res_partner_title.update({ d[0]: exist[0].id})
            else:
                created = self.env['res.partner.title'].create({
                    'name': d[1],
                    'shortcut': d[2]
                })
                res_partner_title.update({ d[0]: created.id})

        # res_partner
        res_partner = {}
        """
            id, name, company_id, reviewer, institution, full_name, display_name,
            date, title, parent_id, ref, lang, tz, user_id,
            vat, website, comment, active, customer, supplier, employee,
            function, type, street, street2, zip, city, state_id, country_id,
            email, phone, mobile, is_company, industry_id, color, partner_share,
            
            #commercial_partner_id, commercial_partner_country_id, commercial_company_name, company_name,
            #create_uid, create_date, write_uid, write_date,

            activity_date_deadline, message_last_post timestamp, message_bounce, opt_out, gender,
            signup_token, signup_type, signup_expiration, website_meta_title, website_meta_description, website_meta_keywords, website_published, website_description, website_short_description,
            team_id, osm_bbox, osm_marker, debit_limit, last_time_entries_checked, invoice_warn, invoice_warn_msg, sale_warn, sale_warn_msg ,
            last_website_so_id, event_track_count, event_track_author_count, event_track_done_count, calendar_last_notif_ack,
        """
        cr.execute("""select id, name, company_id, reviewer, institution, full_name, display_name, 
                    date, title, parent_id, ref, lang, tz, user_id, 
                    vat, website, comment, active, customer, supplier, employee, 
                    function, type, street, street2, zip, city, state_id, country_id,
                    email, phone, mobile, is_company, industry_id, color, partner_share,
                    activity_date_deadline, message_last_post, message_bounce, opt_out, gender,
                    signup_token, signup_type, signup_expiration, website_meta_title, website_meta_description, website_meta_keywords, website_published, website_description, website_short_description,
                    team_id, osm_bbox, osm_marker, debit_limit, last_time_entries_checked, invoice_warn, invoice_warn_msg, sale_warn, sale_warn_msg,
                    last_website_so_id, event_track_count, event_track_author_count, event_track_done_count, calendar_last_notif_ack

                    from res_partner where true order by id asc;""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['res.partner'].search([('name' , '=', d[1]), ('email', '=', d[29]),'|',('active' , '=', True),('active' , '=', False)])
            if exist:
                res_partner.update({ d[0]: exist[0].id})
            else:
                cr.execute("""select store_fname from ir_attachment where res_model = 'res.partner' and res_field = 'image' and res_id = """ + str(d[0]) +""" limit 1;""")
                image = cr.fetchall()
                image_data = False
                if image:
                    try:
                        image_file = open(self.src_filestore + '/'+ image[0][0],'rb')
                        image_data = base64.b64encode(image_file.read())
                        image_file.close()
                    except:
                        pass

                created = self.env['res.partner'].create({
                    'name': d[1],
                    'company_id': d[2],
                    'reviewer': d[3],
                    'institution': d[4],
                    'full_name': d[5],
                    'display_name': d[6],
                    'date': d[7],
                    'title': d[8] and res_partner_title[d[8]] or False,
                    #'parent_id': d[9],
                    'ref': d[10],
                    'lang': d[11],
                    'tz': d[12],
                    #'user_id': d[13],
                    'vat': d[14],
                    #'website': d[15], 
                    'comment': d[16], 
                    'active': True,
                    #'customer': d[18], 
                    #'supplier': d[19], 
                    #'employee': d[20],
                    #'function': d[21], 
                    'type': d[22], 
                    'street': d[23], 
                    'street2': d[24],
                    'zip': d[25],
                    'city': d[26],
                    'state_id': d[27] and res_country_state[d[27]] or False,
                    'country_id': d[28] and res_country[d[28]] or country_cu.id,
                    'email': d[29], 
                    'phone': d[30], 
                    'mobile': d[31], 
                    'is_company': d[32], 
                    #'industry_id': d[33], 
                    'color': d[34], 
                    'partner_share': d[35],
                    'activity_date_deadline': d[36], 
                    #'message_last_post': d[37], 
                    'message_bounce': d[38], 
                    #'opt_out': d[39], 
                    'gender': d[40],
                    'signup_token': d[41],
                    'signup_type': d[42],
                    'signup_expiration': d[43],
                    'website_meta_title': d[44],
                    'website_meta_description': d[45],
                    'website_meta_keywords': d[46],
                    'website_published': d[47],
                    'website_description': d[48],
                    'website_short_description': d[49],  
                    'team_id': d[50],
                    'osm_bbox': d[51],
                    'osm_marker': d[52],
                    'debit_limit': d[53],
                    'last_time_entries_checked': d[54],
                    'invoice_warn': d[55],
                    'invoice_warn_msg': d[56],
                    'sale_warn': d[57],
                    'sale_warn_msg': d[58],
                    'last_website_so_id': d[59],
                    'event_track_count': d[60],
                    'event_track_author_count': d[61],
                    'event_track_done_count': d[62],
                    #'calendar_last_notif_ack': d[63],
                    'image_1920': image_data
                })
                res_partner.update({d[0]: created.id})
        
            self.env.cr.commit()
        
        # res_users
        res_users = {}
        
        default_user_id = self.env['ir.model.data'].xmlid_to_res_id('base.default_user', raise_if_not_found=False)
        user_groups = self.env['res.users'].browse(default_user_id).sudo().groups_id if default_user_id else []

        portal_user_id = self.env['ir.model.data'].xmlid_to_res_id('base.template_portal_user_id', raise_if_not_found=False)
        portal_groups = self.env['res.users'].browse(portal_user_id).sudo().groups_id if portal_user_id else []
        
        cr.execute("""select u.id,
            active,
            login,
            password,
            company_id,
            partner_id,
            signature,
            action_id,
            share,            
            password_crypt,
            chatter_position,
            sidebar_visible,
            alias_id,
            notification_type,
            sale_team_id,
            target_sales_won,
            target_sales_done, log.create_date from res_users AS u left outer join res_users_log AS log on log.create_uid=u.id where u.id > 5 order by id asc;""")
        
        data = cr.fetchall()
        for d in data:
            exist = self.env['res.users'].with_context(lang='en_US').search([('login' , '=', d[2]),'|',('active' , '=', True),('active' , '=', False)])
            if exist:
                res_users.update({ d[0]: exist[0].id})
            else:
                # check if user is portal user
                cr.execute("""select gid from res_groups_users_rel where uid = %s;""" %d[0])
                src_groups = cr.fetchall()
                if (9,) in src_groups:
                    groups = portal_groups
                else:
                    groups = user_groups

                created = self.env['res.users'].create({
                    'login': d[2],
                    'password': d[9], # password_crypt --> password
                    'company_id': d[4],
                    'partner_id': d[5] and res_partner[d[5]] or False,
                    'signature': d[6],
                    #'action_id': d[7],
                    #'share': d[8],
                    #'password_crypt': d[9],
                    #'chatter_position': d[10],
                    #'sidebar_visible': d[11],
                    #'alias_id': d[12],
                    'notification_type': d[13],
                    #'sale_team_id': d[14],
                    #'target_sales_won': d[15],
                    #'target_sales_done': d[16]
                    'groups_id': groups
                    
                })
                res_users.update({d[0]: created.id})
                if d[17]:
                    self.env.cr.execute("INSERT INTO res_users_log(create_uid, create_date, write_uid, write_date) VALUES (%s, '%s', %s, '%s');" %(created.id, d[17], created.id, d[17]))

            self.env.cr.commit()
        
        # event_stage
        event_stage = {}
        """v11 scheme
        <none>
        this model is new in v14, to replace event.state field
        """
        data = [('draft', 'New'), ('cancel', 'Cancelled'), ('confirm', 'Booked'), ('done', 'Ended')]
        for d in data:
            exist = self.env['event.stage'].with_context(lang='en_US').search([('name' , '=', d[1])])
            if exist:
                event_stage.update({d[0]: exist[0].id})
            
        # event_type
        event_type = {}

        """ v11 schema
        id integer NOT NULL DEFAULT nextval('event_type_id_seq'::regclass),
        name character varying NOT NULL, -- Event Category
        has_seats_limitation boolean, -- Limited Seats
        default_registration_min integer, -- Minimum Registrations
        default_registration_max integer, -- Maximum Registrations
        auto_confirm boolean, -- Automatically Confirm Registrations
        is_online boolean, -- Online Event
        use_timezone boolean, -- Use Default Timezone
        default_timezone character varying, -- Timezone
        use_hashtag boolean, -- Use Default Hashtag
        default_hashtag character varying, -- Twitter Hashtag
        use_mail_schedule boolean, -- Automatically Send Emails
        create_uid integer, -- Created by
        create_date timestamp without time zone, -- Created on
        write_uid integer, -- Last Updated by
        write_date timestamp without time zone, -- Last Updated on
        website_menu boolean, -- Display a dedicated menu on Website
        website_registration boolean, -- Registration on Website
        website_track boolean, -- Tracks on Website
        website_track_proposal boolean, -- Tracks Proposals on Website
        use_ticketing boolean, -- Ticketing
        """

        cr.execute("""select id,
        name,
        has_seats_limitation,
        default_registration_min,
        default_registration_max,
        auto_confirm,
        is_online,
        use_timezone,
        default_timezone,
        use_hashtag,
        default_hashtag,
        use_mail_schedule,        
        website_menu,
        website_registration,
        website_track,
        website_track_proposal,
        use_ticketing from event_type where true""")
        
        data = cr.fetchall()
        for d in data:
            exist = self.env['event.type'].with_context(lang='en_US').search([('name' , '=', d[1])])
            if exist:
                event_type.update({d[0]: exist[0].id})
            else:
                # TODO: Improve data defaults
                created = self.env['event.type'].create({
                    'name': d[1],
                    #'sequence': d[1],
                    'use_ticket': d[16], # use_ticketing v11
                    'has_seats_limitation': d[2],
                    'seats_max': d[4],
                    'auto_confirm': d[5],
                    'use_timezone': d[7],
                    'default_timezone': d[8],
                    'use_mail_schedule': d[11],                   
                    'website_menu': d[12],
                    #'community_menu': False,
                    'menu_register_cta': d[13],
                    'website_track': d[14],
                    'website_track_proposal': d[15],
                    'website_registration': d[13],
                })
                event_type.update({d[0]: created.id})

                # import translations of event_type name
                cr.execute("""select src, value, state, module from ir_translation where lang='es_ES' and name = 'event.type,name' and type = 'model' and res_id = """ + str(d[0]) +""" limit 1;""")
                src_trans = cr.fetchall()
                for src_t in src_trans:
                    dst_t = self.env['ir.translation'].search([('name', '=', 'event.type,name'),('lang', '=', 'es_ES'),('res_id','=', created.id)])
                    if dst_t:
                        dst_t.write({
                        'src': src_t[0],
                        'value': src_t[1],
                        'state': src_t[2]                        
                    })
        # res_lang
        res_lang = {}
        cr.execute("""select id, iso_code from res_lang where true""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['res.lang'].with_context(lang='en_US').search([('iso_code' , '=', d[1])])
            if exist:
                res_lang.update({d[0]: exist[0].id})
            
        # event_event
        event_event = {}

        """
        v11 schema
        0   id integer NOT NULL DEFAULT nextval('event_event_id_seq'::regclass),
        1   name character varying NOT NULL, -- Event Name
        2   short_name character varying, -- Event Short Name
        3   subname character varying, -- Event Sub Name
        4   "number" character varying, -- Number
        5   active boolean, -- Active
        6   user_id integer NOT NULL, -- Responsible
        7   company_id integer, -- Company
        8   organizer_id integer, -- Organizer
        9   event_type_id integer, -- Category
        10  color integer, -- Kanban Color Index
        11  seats_max integer, -- Maximum Attendees Number
        12  seats_availability character varying NOT NULL, -- Maximum Attendees
        13  seats_min integer, -- Minimum Attendees
        14  seats_reserved integer, -- Reserved Seats
        15  seats_available integer, -- Available Seats
        16  seats_unconfirmed integer, -- Unconfirmed Seat Reservations
        17  seats_used integer, -- Number of Participants
        18  date_tz character varying NOT NULL, -- Timezone
        19  date_begin timestamp without time zone NOT NULL, -- Start Date
        20  date_end timestamp without time zone NOT NULL, -- End Date
        21  state character varying NOT NULL, -- Status
        22  auto_confirm boolean, -- Autoconfirm Registrations
        23  is_online boolean, -- Online Event
        24  address_id integer, -- Location
        25  country_id integer, -- Country
        26  twitter_hashtag character varying, -- Twitter Hashtag
        27  description text, -- Description
        28  badge_front text, -- Badge Front
        29  badge_back text, -- Badge Back
        30  badge_innerleft text, -- Badge Inner Left
        31  badge_innerright text, -- Badge Inner Right
        32  event_logo text, -- Event Logo
        33  message_last_post timestamp without time zone, -- Last Message Date        
        34  website_published boolean, -- Visible in Website
        35  website_menu boolean, -- Dedicated Menu
        36  menu_id integer, -- Event Menu
        37  website_meta_title character varying, -- Website meta title
        38  website_meta_description text, -- Website meta description
        39  website_meta_keywords character varying, -- Website meta keywords
        40  website_registration_ok boolean, -- Registration on Website
        41  website_track_ok boolean, -- Tracks on Website
        42  website_track_proposal_ok boolean, -- Proposals on Website
        43  website_track_proposal_msg text, -- Proposal Message
        44  website_track_proposal_template bytea, -- Proposal Template
        45  website_track_proposal_deadline timestamp without time zone, -- Proposals Deadline
        46  coordinator character varying, -- Coordinator
        47  correo character varying, -- Correo
        48  website_introduction_msg text, -- Introduction Message
        49  email character varying, -- Email
        """

        cr.execute("""select id, name, short_name, subname, number,
        active, user_id, company_id, organizer_id,
        event_type_id, color, seats_max, seats_availability,
        seats_min, seats_reserved, seats_available, seats_unconfirmed,
        seats_used, date_tz, date_begin, date_end, state, auto_confirm, is_online,
        address_id, country_id, twitter_hashtag, description,
        badge_front, badge_back, badge_innerleft, badge_innerright,
        event_logo, message_last_post, website_published, website_menu,
        menu_id, website_meta_title, website_meta_description, website_meta_keywords,
        website_registration_ok, website_track_ok, website_track_proposal_ok, website_track_proposal_msg,
        website_track_proposal_template, website_track_proposal_deadline, coordinator, correo, website_introduction_msg,
        email from event_event where true order by id""")
        
        data = cr.fetchall()
        for d in data:
            exist = self.env['event.event'].with_context(lang='en_US').search([('name' , '=', d[1]),('short_name' , '=', d[2]),('subname' , '=', d[3]),'|',('active' , '=', True),('active' , '=', False)])
            if exist:
                event_event.update({d[0]: exist[0].id})
            else:
                cr.execute("""select store_fname from ir_attachment where res_model = 'event.event' and res_field = 'image' and res_id = """ + str(d[0]) +""" limit 1;""")
                image = cr.fetchall()
                image_data = False
                if image:
                    try:
                        image_file = open(self.src_filestore + '/'+ image[0][0],'rb')
                        image_data = base64.b64encode(image_file.read())
                        image_file.close()
                    except:
                        pass
                
                created = self.env['event.event'].with_context(ignore_errors=True).create({
                    'name': d[1],
                    #'note'
                    'description': d[27],
                    'active': d[5],
                    'user_id': res_users[d[6]],
                    'company_id': d[7],
                    'organizer_id': res_partner[d[8]],
                    'event_type_id': d[9] and event_type[d[9]] or False,
                        #'kanban_state':
                        #'kanban_state_label
                    'stage_id': event_stage.get(d[21], '1'),
                    'seats_max': d[11],
                    'seats_limited': d[12], # v11 seats_availability
                    'seats_reserved': d[14],
                    'seats_available': d[15],
                    'seats_unconfirmed': d[16],
                    'seats_used': d[17],
                    'auto_confirm': d[22],
                    'date_tz': d[18],
                    'date_begin': d[19],
                    'date_end': d[20],
                    'address_id': d[24] and res_partner[d[24]] or False,
                    'country_id': d[25] and res_country[d[25]] or False,
                    'badge_front': d[28],
                    'badge_back': d[29],
                    'badge_innerleft': d[30],
                    #'badge_innerrigh': d[31], #ignore this
                    'event_logo': d[32],
                        #'message_main_attachment_id':                    
                    'short_name': d[2],
                    'subname': d[3],
                    'number': d[4],
                    'website_meta_title': d[37],
                    'website_meta_description': d[38],
                    'website_meta_keywords': d[39],
                    #'website_meta_og_img':
                    #'seo_name':
                    'cover_properties': '{"background-image":"url(/website_event_uclv/static/src/img/screenshot' + str(d[0]%4) + '.jpg)","background_color_class":"o_cc3","background_color_style":"","opacity":"0.4","resize_class":"o_half_screen_height","text_align_class":""}',
                    #'website_id':
                    'is_published': d[5],
                    #'subtitle':
                    'website_menu': d[35],
                    #'menu_id': d[36], # ignore this
                    #'menu_register_cta':
                    #'community_menu':
                    'website_track': d[41], # v11 website_track_ok
                    'website_track_proposal': d[42], #v11 website_track_proposal_ok
                    'email': d[49],
                    'website_registration_ok': d[40],
                    'paper_abstract_deadline': d[45], # v11 website_track_proposal_deadline
                    'paper_abstract_notification_date': d[45], # workaround
                    'paper_final_deadline': d[45], # workaround
                    'image_1920': image_data,                    
                })
                event_event.update({d[0]: created.id})

                # import translations of event_event name
                cr.execute("""select src, value, state, module from ir_translation where lang='es_ES' and name = 'event.event,name' and type = 'model' and res_id = """ + str(d[0]) +""" limit 1;""")
                src_trans = cr.fetchall()
                for src_t in src_trans:
                    dst_t = self.env['ir.translation'].search([('name', '=', 'event.event,name'),('lang', '=', 'es_ES'),('res_id','=', created.id)])
                    if dst_t:
                        dst_t.write({
                        'src': src_t[0],
                        'value': src_t[1],
                        'state': src_t[2]
                    })
                # import translations of event_event subname
                cr.execute("""select src, value, state, module from ir_translation where lang='es_ES' and name = 'event.event,subname' and type = 'model' and res_id = """ + str(d[0]) +""" limit 1;""")
                src_trans = cr.fetchall()
                for src_t in src_trans:
                    dst_t = self.env['ir.translation'].search([('name', '=', 'event.event,subname'),('lang', '=', 'es_ES'),('res_id','=', created.id)])
                    if dst_t:
                        dst_t.write({
                        'src': src_t[0],
                        'value': src_t[1],
                        'state': src_t[2]
                    })
                # import translations of event_event short_name
                cr.execute("""select src, value, state, module from ir_translation where lang='es_ES' and name = 'event.event,short_name' and type = 'model' and res_id = """ + str(d[0]) +""" limit 1;""")
                src_trans = cr.fetchall()
                for src_t in src_trans:
                    dst_t = self.env['ir.translation'].search([('name', '=', 'event.event,short_name'),('lang', '=', 'es_ES'),('res_id','=', created.id)])
                    if dst_t:
                        dst_t.write({
                        'src': src_t[0],
                        'value': src_t[1],
                        'state': src_t[2]
                    })
            self.env.cr.commit()
        
        # event_allowed_language_rel
        cr.execute("""select event_event_id, res_lang_id from event_allowed_language_rel where true""")
        data = cr.fetchall()
        for d in data:
            if event_event.get(d[0], False) and res_lang.get(d[1], False):
                self.env.cr.execute("select count(*) from event_allowed_language_rel where event_event_id=%s and res_lang_id=%s" %(event_event[d[0]], res_lang[d[1]]))
                count = self.env.cr.fetchall()
                if not count[0][0]:
                    self.env.cr.execute("insert into event_allowed_language_rel(event_event_id, res_lang_id) VALUES (%s, %s);" %(event_event[d[0]], res_lang[d[1]]))
                    self.env.cr.commit()
                    
        # event_sponsor
        event_sponsor = {}
        """
        v11 schema
        
        0   id integer NOT NULL DEFAULT nextval('event_sponsor_id_seq'::regclass),
        1   event_id integer NOT NULL, -- Event
        2   sponsor_type_id integer NOT NULL, -- Sponsoring Type
        3   partner_id integer NOT NULL, -- Sponsor/Customer
        4   url character varying, -- Sponsor Website
        5   sequence integer, -- Sequence
        """
        cr.execute("""select id, event_id, sponsor_type_id, partner_id, url, sequence from event_sponsor where true""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['event.sponsor'].with_context(lang='en_US').search([('event_id' , '=', event_event[d[1]]),('partner_id', '=', res_partner[d[3]])])
            if exist:
                event_sponsor.update({d[0]: exist[0].id})
            else:
                created = self.env['event.sponsor'].create({
                    'event_id': event_event[d[1]],
                    'sponsor_type_id': d[2],
                    'url': d[4],
                    'sequence': d[5],
                    'partner_id': res_partner[d[3]]
                })
                event_sponsor.update({d[0]: created.id})

        # event_track_tag
        event_track_tag = {}
        """
        v11 schema

        id integer NOT NULL DEFAULT nextval('event_track_tag_id_seq'::regclass),
        name character varying, -- Tag
        color integer, -- Color Index
        """
        cr.execute("""select id, name, color from event_track_tag where true""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['event.track.tag'].with_context(lang='en_US').search([('name' , '=', d[1])])
            if exist:
                event_track_tag.update({d[0]: exist[0].id})
            else:
                created = self.env['event.track.tag'].create({
                    'name': d[1],
                    'sequence': 10,
                    'color': randint(1, 11)
                })
                event_track_tag.update({d[0]: created.id})
                
                # TODO: check the posibility of language related tags
            self.env.cr.commit()

        # event_track_location
        event_track_location = {}
        """
        v11 schema

        id integer NOT NULL DEFAULT nextval('event_track_location_id_seq'::regclass),
        name character varying, -- Room        
        partner_id integer, -- Partner
        """
        cr.execute("""select id, name, partner_id from event_track_location where true""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['event.track.location'].with_context(lang='en_US').search([('name' , '=', d[1]), ('partner_id' , '=', res_partner[d[2]])])
            if exist:
                event_track_location.update({d[0]: exist[0].id})
            else:
                created = self.env['event.track.location'].create({
                    'name': d[1],
                    'partner_id': d[2] and res_partner[d[2]] or False
                })
                event_track_location.update({d[0]: created.id})

        # event_track_type
        event_track_type = {}
        """
        v11 schema
        id integer NOT NULL DEFAULT nextval('event_track_type_id_seq'::regclass),
        name character varying NOT NULL, -- Name
        description character varying, -- Description
        
        """
        cr.execute("""select id, name, description from event_track_type where true""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['event.track.type'].with_context(lang='en_US').search([('name' , '=', d[1])])
            if exist:
                event_track_type.update({d[0]: exist[0].id})
            else:
                created = self.env['event.track.type'].create({
                    'name': d[1],
                    'description': d[2],
                })
                event_track_type.update({d[0]: created.id})

        # event_track
        event_track = {}

        """
        v11 schema

        0   id integer NOT NULL DEFAULT nextval('event_track_id_seq'::regclass),
        1   name character varying NOT NULL, -- Title
        2   active boolean, -- Active
        3   publish_complete boolean, -- Can be Published
        4   user_id integer, -- First Reviewer
        5   user2_id integer, -- Second Reviewer
        6   partner_id integer, -- Speaker
        7   partner_biography text, -- Speaker Biography
        8   stage_id integer NOT NULL, -- Stage
        9   kanban_state character varying NOT NULL, -- Kanban State
        10  description text, -- Track Description
        11  date timestamp without time zone, -- Track Date
        12  language_id integer, -- Language
        13  duration double precision, -- Duration
        14  location_id integer, -- Room
        15  event_id integer NOT NULL, -- Event
        16  color integer, -- Color Index
        17  priority character varying NOT NULL, -- Priority
        18  message_last_post timestamp without time zone, -- Last Message Date
        19  website_meta_title character varying, -- Website meta title
        20  website_meta_description text, -- Website meta description
        21  website_meta_keywords character varying, -- Website meta keywords
        22  website_published boolean, -- Visible in Website
        23  activity_date_deadline date, -- Next Activity Deadline
        24  coordinator_notes text, -- Notes for the Coordinator
        25  author_notes text, -- Notes for the Author
        26  recommendation character varying, -- Recommendation
        27  coordinator_notes2 text, -- Notes for the Coordinator
        28  author_notes2 text, -- Notes for the Author
        29  recommendation2 character varying, -- Recommendation
        30  revision_status integer, -- status
        31  revision_status2 integer, -- status2
        32  reviewer_id integer, -- First Reviewer
        33  reviewer2_id integer, -- Second Reviewer
        34  partner_name character varying, -- Speaker Name
        35  partner_email character varying, -- Speaker Email
        36  partner_phone character varying, -- Speaker Phone
        37  track_type_id integer, -- Track Type
        38  multiple boolean, -- Multiple
        39  authenticity_token character varying, -- Authenticity Token
        """
        # fix empty authenticity_token on src db
        cr.execute("""select id from event_track where authenticity_token='';""")
        data = cr.fetchall()
        for d in data:
            cr.execute("""update event_track set authenticity_token='%s' where id=%s;""" %(uuid.uuid4(), d[0]))

        cr.execute("""select id, name, active, publish_complete, user_id, user2_id, partner_id, partner_biography,
        stage_id, kanban_state, description, date, language_id, duration, location_id, event_id, color,
        priority, message_last_post, website_meta_title, website_meta_description, website_meta_keywords, website_published,
        activity_date_deadline, coordinator_notes, author_notes, recommendation, coordinator_notes2, author_notes2,
        recommendation2, revision_status, revision_status2, reviewer_id, reviewer2_id, partner_name,
        partner_email, partner_phone, track_type_id, multiple, authenticity_token
         from event_track where true order by id;""")
        data = cr.fetchall()
        for d in data:
            exist = self.env['event.track'].with_context(lang='en_US').search([('authenticity_token' , '=', d[39])])
            if exist:
                event_track.update({d[0]: exist[0].id})
            else:
                if not d[6]:
                    print("NO partner found for event_track: %s" %d[39])
                else:
                    created = self.env['event.track'].sudo().with_context({'ignore_errors': True, 'no_message': True}).create({
                        'name':d[1], 
                        'active': d[2], 
                        'publish_complete': d[3],
                        #'reviewer_id': d[4] and res_users[d[4]] or False, 
                        #'reviewer2_id': d[5] and res_users[d[5]] or False, 
                        'partner_id': d[6] and res_partner[d[6]] or False, 
                        #'partner_biography': d[7],
                        'stage_id': d[8],
                        'kanban_state': d[9], 
                        'description': d[10],
                        'description_es': d[10],
                        'date': d[11], 
                        'language_id': d[12] and res_lang.get(d[12], False) or False, 
                        'duration': d[13],  
                        'location_id': d[14] and event_track_location[d[14]] or False,  
                        'event_id': event_event[d[15]], 
                        'color': d[16], 
                        'priority': d[17], 
                        #'message_last_post': d[18], 
                        'website_meta_title': d[1],  #name
                        'website_meta_description': d[10], #description 
                        'website_meta_keywords': d[21], # TODO: update with tags???
                        'is_published': d[22], 
                        'activity_date_deadline': d[23],  
                        #'coordinator_notes': d[24],  
                        #'author_notes': d[25],  
                        #'recommendation': d[26],  
                        #'coordinator_notes2': d[27],  
                        #'author_notes2': d[28], 
                        #'recommendation2': d[29],  
                        #'revision_status': d[30],  
                        #'revision_status2': d[31],  
                        #'reviewer_id': d[32] and res_users[d[32]] or False, 
                        #'reviewer2_id': d[33] and res_users[d[33]] or False, 
                        'partner_name': d[34], 
                        'partner_email': d[35], 
                        'partner_phone': d[36], 
                        'track_type_id': d[37] and event_track_type[d[37]] or False,
                        #'multiple': d[38], 
                        'authenticity_token': d[39]
                    })

                    #import attachments
                    cr.execute("""select store_fname, name, public from ir_attachment where res_model = 'event.track' and res_field is null and res_id = """ + str(d[0]))
                    attachments = cr.fetchall()                    
                    for a in attachments:
                        try:
                            a_file = open(self.src_filestore + '/'+ a[0],'rb')
                            a_data = base64.b64encode(a_file.read())
                            a_file.close()

                            self.env['ir.attachment'].create(
                                {
                                    'res_model': 'event.track',
                                    'res_id': created.id,
                                    'name': d[1],
                                    'description': d[1],
                                    'public': d[2],
                                    'datas': a_data
                                })
                        except:
                            pass

                    """                                      
                    date_end timestamp without time zone, -- Track End Date
                    access_token character varying, -- Security Token                    
                    """
                    event_track.update({d[0]: created.id})

                    # import translations of event_track name
                    cr.execute("""select src, value, state, module from ir_translation where lang='es_ES' and name = 'event.track,name' and type = 'model' and res_id = """ + str(d[0]) +""" limit 1;""")
                    src_trans = cr.fetchall()
                    for src_t in src_trans:
                        dst_t = self.env['ir.translation'].search([('name', '=', 'event.track,name'),('lang', '=', 'es_ES'),('res_id','=', created.id)])
                        if dst_t:
                            dst_t.write({
                            'src': src_t[0],
                            'value': src_t[1],
                            'state': src_t[2]
                        })
            self.env.cr.commit()

                    

        # event_track_event_track_tag_rel
        cr.execute("""select event_track_tag_id, event_track_id from event_track_event_track_tag_rel where true""")
        data = cr.fetchall()
        for d in data:
            if event_track.get(d[1], False):
                self.env.cr.execute("select count(*) from event_track_event_track_tag_rel where event_track_tag_id=%s and event_track_id=%s" %(event_track_tag[d[0]], event_track[d[1]]))
                count = self.env.cr.fetchall()
                if not count[0][0]:
                    self.env.cr.execute("insert into event_track_event_track_tag_rel(event_track_tag_id, event_track_id) VALUES (%s, %s);" %(event_track_tag[d[0]], event_track[d[1]]))
                    self.env.cr.commit()

        # event_track_res_partner_rel
        cr.execute("""select event_track_id, res_partner_id from event_track_res_partner_rel where true""")
        data = cr.fetchall()
        for d in data:
            if event_track.get(d[0], False) and res_partner.get(d[1], False):
                self.env.cr.execute("select count(*) from event_track_author where track_id=%s and partner_id=%s" %(event_track[d[0]], res_partner[d[1]]))
                count = self.env.cr.fetchall()
                if not count[0][0]:
                    et = self.env['event.track'].browse(event_track[d[0]])
                    self.env.cr.execute("insert into event_track_author(track_id, partner_id, sequence) VALUES (%s, %s, %s);" %(event_track[d[0]], res_partner[d[1]], len(et.author_ids)))
                    self.env.cr.commit()
        
  




        
    