# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
import werkzeug

from odoo import http, tools, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.exceptions import UserError
from odoo.http import request


_logger = logging.getLogger(__name__)


class UCLVAuthSignupHome(AuthSignupHome):
    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        qcontext.update({'countries': request.env['res.country'].sudo().search([])})
        qcontext.update({'states': request.env['res.country.state'].sudo().search([])})
        qcontext.update({'titles': request.env['res.partner.title'].sudo().search([])})
        if not qcontext.get('token') and not qcontext.get('signup_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                self.do_signup(qcontext)
                # Send an account creation confirmation email
                if qcontext.get('token'):
                    User = request.env['res.users']
                    user_sudo = User.sudo().search(
                        User._get_login_domain(qcontext.get('login')), order=User._get_login_order(), limit=1
                    )
                    template = request.env.ref('auth_signup.mail_template_user_signup_account_created', raise_if_not_found=False)
                    if user_sudo and template:
                        template.sudo().send_mail(user_sudo.id, force_send=True)
                return self.web_login(*args, **kw)
            except UserError as e:
                qcontext['error'] = e.args[0]
            except (SignupError, AssertionError) as e:
                if request.env["res.users"].sudo().search([("login", "=", qcontext.get("login"))]):
                    qcontext["error"] = _("Another user is already registered using this email address.")
                else:
                    _logger.error("%s", e)
                    qcontext['error'] = _("Could not create a new account.")

        response = request.render('auth_signup.signup', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @http.route('/web/reset_password', type='http', auth='public', website=True, sitemap=False)
    def web_auth_reset_password(self, *args, **kw):
        qcontext = self.get_auth_signup_qcontext()
        qcontext.update({'countries': request.env['res.country'].sudo().search([])})
        qcontext.update({'states': request.env['res.country.state'].sudo().search([])})
        qcontext.update({'titles': request.env['res.partner.title'].sudo().search([])})
        
        if not qcontext.get('token') and not qcontext.get('reset_password_enabled'):
            raise werkzeug.exceptions.NotFound()

        if 'error' not in qcontext and request.httprequest.method == 'POST':
            try:
                if qcontext.get('token'):
                    self.do_signup(qcontext)
                    return self.web_login(*args, **kw)
                else:
                    login = qcontext.get('login')
                    assert login, _("No login provided.")
                    _logger.info(
                        "Password reset attempt for <%s> by user <%s> from %s",
                        login, request.env.user.login, request.httprequest.remote_addr)
                    request.env['res.users'].sudo().reset_password(login)
                    qcontext['message'] = _("An email has been sent with credentials to reset your password")
            except UserError as e:
                qcontext['error'] = e.name or e.value
            except SignupError:
                qcontext['error'] = _("Could not reset your password")
                _logger.exception('error when resetting password')
            except Exception as e:
                qcontext['error'] = str(e)

        response = request.render('auth_signup.reset_password', qcontext)
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """

        if qcontext.get('token'):
            values = { key: qcontext.get(key) for key in ('login', 'name', 'password')}
        else:
            values = { key: qcontext.get(key) for key in ('login', 'name', 'password', 'phone', 'country_id', 'institution', 'title', 'gender') }
            values.update({'country_id': int(values.get('country_id', 0))})
            if values.get('title', 0):
                values.update({'title': int(values.get('title', 0))})
            else:
                values.update({'title': False})
        if not values:
            raise UserError(_("The form was not properly filled in."))        
        
        
        
        if values.get('login') and not tools.single_email_re.match(values.get('login')):
            raise UserError(_('Invalid Email! Please enter a valid email address.'))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '').split('_')[0]
        if lang in supported_lang_codes:
            values['lang'] = lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()

    def _signup_with_values(self, token, values):
        db, login, password = request.env['res.users'].sudo().signup(values, token)
        request.env.cr.commit()     # as authenticate will use its own cursor we need to commit the current transaction
        uid = request.session.authenticate(db, login, password)
        if not uid:
            raise SignupError(_('Authentication Failed.'))