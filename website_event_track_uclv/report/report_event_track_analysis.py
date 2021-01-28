# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class ReportEventTrackAnalysis(models.Model):
    _name = 'report.event.track.analysis'
    _auto = False

    event_name = fields.Char(string="Main Event", readonly=True, translate=True)
    event_id = fields.Many2one('event.event', string='Event', readonly=True)
    track_id = fields.Many2one('event.track', string='Track', readonly=True)
    author_id = fields.Many2one('res.partner', string='Author', readonly=True)
    author_user_id = fields.Many2one('res.users', string='User', readonly=True)
    author_country_id = fields.Many2one('res.country', string='Author Country', readonly=True)
    author_institution = fields.Char(string='Author Institution', readonly=True)
    author_email = fields.Char(string='Author Email', readonly=True)
    coordinator_id = fields.Many2one('res.users', string='Coordinator', readonly=True)
    language_id  = fields.Many2one('res.lang', string='Track Language', readonly=True)
    track_stage_id = fields.Many2one('event.track.stage', string="Track Stage", readonly=True)
    track_stage_ok = fields.Boolean(string="Track Accepted", readonly=True)

    """@api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        company_ids = [c.id for c in self.env["res.company"].search([('parent_id', '=', self.env.user.company_id.id)])]
        company_ids.append(self.env.user.company_id.id)
        domain.append(("company_id", "in", company_ids))
        return super(ReportExistenceAnalysis,self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):        
        new_args = []
        company_ids = [c.id for c in self.env["res.company"].search([('parent_id', '=', self.env.user.company_id.id)])]
        company_ids.append(self.env.user.company_id.id)
        
        new_args.append(("company_id", "in", company_ids))
        for arg in args:
            new_args.append(arg)

        return super(ReportExistenceAnalysis, self).search(new_args, offset=offset, limit=limit, order=order, count=count)
    """
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_event_track_analysis')
        self._cr.execute("""CREATE or REPLACE VIEW report_event_track_analysis AS (
                 SELECT
                        track.id as id,
                        track.id as track_id,
                        event.id as event_id,
                        event.name as event_name,
                        author.id as author_id,
                        author_user.id as author_user_id,
                        country.id as author_country_id,
                        resp.id as coordinator_id,
                        lang.id as language_id,
                        author.institution as author_institution,
                        author.email as author_email,
                        stage.id as track_stage_id,
                        stage.is_done as track_stage_ok
                    FROM
                        event_track track
                        LEFT JOIN event_event event ON (track.event_id=event.id)
                        LEFT JOIN res_partner author ON (track.partner_id=author.id)
                        LEFT JOIN res_country country ON (author.country_id=country.id)
                        LEFT JOIN res_users resp ON (event.user_id=resp.id)
                        LEFT JOIN res_users author_user ON (author_user.partner_id=author.id)
                        LEFT JOIN res_lang lang ON (track.language_id=lang.id)
                        LEFT JOIN event_track_stage stage ON (track.stage_id=stage.id)
                    WHERE true
                    GROUP BY
			            event.id,
                        event.name,
                        track.id,
                        author_user.id,
                        author.id,
                        author.institution,
                        author.email,
                        country.id,
                        resp.id,
                        lang.id,
                        stage.id,
                        stage.is_done
                )""")
