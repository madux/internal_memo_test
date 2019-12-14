#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      kingston
#
# Created:     20/04/2018
# Copyright:   (c) kingston 2018
# Licence:     <your licence>

"""The Employee incharge creates a memo and sends it to the

    **** Manager ===> COO Approval ===> accountant
    **** Account selects the type of payment... Onselection, Button of supplier, customer refund, view payment opens on each states (use context in hotel restaurant folio is a guest)

    """
#-------------------------------------------------------------------------------
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import except_orm, ValidationError

from datetime import datetime, timedelta
import time


class Account_invoice(models.Model):
    _inherit = "account.invoice"

    '''@api.multi
    def name_get(self):
        result = []
        for record in self:
            namey = record.number
            if record.amount_total:
                names = "[INV:" +str(record.number)+"] [TOTAL:" + str(record.amount_total)+ "] [DATE:" +str(record.date_invoice)
                result.append((record.id, names))
        return result
    '''

    @api.multi
    def name_get(self):
        if not self.ids:
            return []
        res=[]
        for field6 in self.browse(self.ids):
            name = field6.number
            nam = "[Name: "+str(name)
            res.append((field6.id, nam +"]    Date: ["+str(field6.date_invoice)+"]"))
        return res


class MemoStarter(models.Model):
    _name = 'internal.memo.custom'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    @api.onchange('vendor_bill')
    def _get_source_amount(self):
        self.update({'amountfig':self.vendor_bill.amount_total})

    @api.multi
    def send_direct_message(self):
        template = self.env['ir.model.data'].get_object('mail_test_memo', 'memo_email_template')
        sender =self.env['mail.template'].browse(template.id).send_mail(self.id)
        self.env['mail.mail'].browse(sender).send(sender)
        return True
    @api.model
    def _needaction_domain_get(self):

        if self.env.user == "Administrator":
            return False  # don't show to Bob!
        return [('state', 'in', ['headunit','manager'])]

    '''@api.model
    def _needaction_count(self, domain=None):
        """
         Show a count of draft state reservations on the menu badge.
         """
        return self.search_count([('state', 'not in', ['submit','headunit','manager','ed','coo','account','post','done','refused'])]) '''

    def _get_requester(self):
        """Return the employee linked with the currently logged in user"""
        empl_obj = self.env['hr.employee']
        user_id = self.env.uid
        return empl_obj.search([('user_id','=', user_id)])

    name = fields.Char('Memo Description')
    date = fields.Datetime(string='Date',default=fields.Date.context_today, required=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string = 'Responsible',default=_get_requester, states={'draft': [('readonly', False)]})
    dept_ids = fields.Char(string ='Department', related='employee_id.department_id.name',readonly = True, store =True)#compute='_department_id',)#related='employee_id.department_id.name', readonly = True, store=True)#
    vendor_bill = fields.Many2one('account.invoice', 'Reference')
    origin_ref = fields.Char(string = 'Memo',related='vendor_bill.origin', store =True) #compute='_memo_id',
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='No. Attachments')
    description = fields.Char('Note')
    project_id = fields.Many2one('account.analytic.account', 'Project')
    amountfig = fields.Float('Amount')#, compute='_get_source_amount')#, related="vendor_bill.amount_total", store=True)
    description_two=fields.Text('Reasons')
    file_upload = fields.Binary('File Upload')


    to_partner=fields.Many2one('res.users', string ="Direct Recipients")


    state = fields.Selection([('submit', 'Draft'),
                                ('headunit', 'HOU'),
                                ('manager', 'GM'),
                                ('ed', 'ED'),
                                ('coo', 'MD/CEO'),
                                ('account', 'Accounts'),
                                ('post', 'Posted'),
                                ('done', 'Paid'),
                                ('refused', 'Refused')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='submit', required=True,
        help='Expense Report State')
    payment_mode = fields.Selection([("csr", "Customer Refund"), ("sp", "Supplier Payment"),("dla", "Direct Labour Payment")], string="Payment Type",required=True,)#, states={'done': [('readonly', True)], 'post': [('readonly', True)]}, string="Payment By")


    @api.multi
    def unlink(self):
        for memo in self.filtered(lambda memo: memo.state not in ['submit', 'refused', 'post']):
            raise ValidationError(_('You cannot delete a Memo which is in %s state.') % (memo.state,))
        return super(Send_Request, self).unlink()
# employee submit to HOU for confirm
    @api.multi
    def button_employee_headunit(self): # vis_hou
        self.state = 'headunit'
        body = "The memo has been submitted to Head of Unit for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
        #records = self._get_followers()
        #followers = records#[self.ids[4]]['message_follower_ids']
        #self.message_post(body=body, subtype='mt_comment', message_type='notification',partner_ids=followers)
        subject ="Memo Notification"

        ########
        partner_ids = self.env['res.users'].browse(self.to_partner).ids
 # search domain to filter specific partners
        self.message_post(subject=subject,body=body, subtype='mt_comment',message_type='notification',partner_ids=partner_ids)#[(4, [partner_ids])])
        ########
# coo / ed to account
# hou submit to Gm

    def send_Gmanager_ed_coo_submit(self):
        one_million = float(1000000)
        if self.amountfig  <= one_million:
            self.write({'state':'ed'})
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

            email_from = self.env.user.email
            email_to = self.employee_id.work_email
            bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been sent to ED for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)

        elif self.amountfig >= one_million:
            self.write({'state':'coo'})
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)
            email_from = self.env.user.email
            email_to = self.employee_id.work_email


            bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been sent to CEO for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)


        else:
            email_from = self.env.user.email
            email_to = self.employee_id.work_email

            bodyx = "Dear Sir/Madam, </br>We wish to notify that the memo from {} has been sent back simply because an amount was not specified for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)

            self.write({'state':'manager'})


    @api.multi
    def button_hou_gmanager(self): # vis_hou_GM
        self.state = 'manager'
        body = "The memo has been submitted to Manager for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment', message_type='notification',partner_ids=followers)
# coo / ed to account

    """
    records = self._get_followers(cr, uid, ids, None, None, context=context)
    followers = records[ids[0]]['message_follower_ids']
    self.message_post(cr, uid, ids, body=body,
            subtype='mt_comment',
            partner_ids=followers,
            context=context)"""
# gm to submit to ED If greater than amount > 1million, to accounts if amount < 1MILLION
# GM manager submit to ed
    @api.multi
    def button_gm_ed(self):
        one_mill = float(1000000)
        if self.amountfig <= one_mill:
            self.state = 'ed'
            body = "The Memo has been submitted to ED for Payment on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)
        elif self.amountfig >= one_mill:
            self.state = 'coo'
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)
        else:
            raise ValidationError('No Amount on the Choosen invoice')


    @api.multi
    def button_ed_to_coo(self):
        one_mill = float(1000000)
        if self.amountfig <= one_mill: # vis_submit
            self.state = 'account'
            body = "The Memo has been submitted to Accounts for Payment on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)
        elif self.amountfig >= one_mill:
            self.state = 'coo'
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)
        else:
            raise ValidationError('No Amount on the Choosen invoice')



# coo / ed to account
    @api.multi
    def button_coo_ed_account(self):#vis_account
        self.state = 'account'
        body = "The Memo has been confirmed and posted to Accounts from %s on %s" % (self.env.user.name,datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

    def message_posts(self):
        body= "REFUSAL NOTIFICATION;\n %s" %(self.description_two)
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

    @api.multi
    def button_account_post(self):#vis_coo
        self.state = 'post'

# coo submit to account

    @api.multi
    def refused_manager(self): #vis_account,
        '''self.state = 'refused'
        body = "General Manager has rejected the Memo on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)'''
        return {
              'name': 'Reason for Refusal',
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'send.memo.message',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': {
                  'default_memo_record': self.id,
                  'default_date': self.date
              },
        }
    @api.multi
    def refused_ed(self): #vis_account,
        '''self.state = 'refused'
        body = "ED has rejected the Memo on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)'''
        return {
              'name': 'Reason for Refusal',
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'send.memo.message',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': {
                  'default_memo_record': self.id,
                  'default_date': self.date
              },
        }
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    '''@api.multi
    def button_dla_pay(self):
        return self.open_payment_form()
    @api.multi
    def open_payment_form(self):

        return {
                'type':'ir.actions.act_window',
                'res_model':'account.payment',
                'res_id':self.id,
                'view_type':'tree',
                'view_mode':'tree',
                'target':'current',
                #'domain': [('partner_id','=', self.partner_id.id)]
                #'context': {'default_memo_record': self.id,'default_date': self.date},
    }'''



    @api.multi
    def refuse_account(self): #vis_account,
        '''self.state = 'refused'
        body = "Account has rejected the Memo on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)'''



        return {
              'name': 'Reason for Refusal',
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'send.memo.message',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': {
                  'default_memo_record': self.id,
                  'default_date': self.date
              },
        }


    @api.multi
    def refuse_coo(self): #vis_account,
        '''self.state = 'refused'
        body = "COO has rejected the Memo on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)'''

        return {
              'name': 'Reason for Refusal',
              'view_type': 'form',
              "view_mode": 'form',
              'res_model': 'send.memo.message',
              'type': 'ir.actions.act_window',
              'target': 'new',
              'context': {
                  'default_memo_record': self.id,
                  'default_date': self.date
              },
        }
    @api.multi
    def button_cancel(self):
        self.state = 'submit'


    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'internal.memo.custom'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'internal.memo.custom'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'internal.memo.custom', 'default_res_id': self.id}
        return res

    @api.onchange('employee_id')
    def _department_id(self):
        for y in self:
            department = y.employee_id.department_id.name
            y.dept_ids = department

    @api.onchange('vendor_bill')
    def _memo_id(self):
        for y in self:
            origin = y.vendor_bill.origin
            y.origin_ref = origin


    '''@api.depends('num_days', 'request_amount', 'payment_mode')
    def _compute_amount_three(self):
        for x in self:
            if x.payment_mode == 'bymonth':
                if x.num_days > 12:
                    raise UserError(_("Month Cannot Exceed 12 calendar Months"))
                else:
                    cal_Month = x.num_days * x.request_amount
                    x.total_amount = cal_Month
            elif x.payment_mode == 'byday':
                cal_day = x.num_days * x.request_amount
                x.total_amount = cal_day'''
    '''@api.multi
    def button_pay_supplier(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('allocation', 'view_payment_action')
        #res['domain'] = [('res_model', '=', 'internal.memo.custom'), ('res_id', 'in', self.ids)]
        #res['context'] = {'default_res_model': 'internal.memo.custom', 'default_res_id': self.id}
        return res'''
    @api.multi
    def button_pay_supplier(self):#vis_post

        #print "########### "+ str(self.vendor_bill)
        xxxxlo = self.env['account.invoice'].search([('id', '=', self.vendor_bill.id)])
        self.write({'state':'done'})
        if not xxxxlo:
            raise except_orm(_('Error'),
                                 _('There is no related bills for this Memo. \
                                 Kindly create a vendor bill and try again.'))
        resp = {
            'type': 'ir.actions.act_window',
            'name': _('Supplier Reference'),
            'res_model': 'account.invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id': xxxxlo.id
        }
        return resp
        '''self.ensure_one()
        res = self.env['ir.actions.act_window.view'].for_xml_id('account', 'action_invoice__supplier_tree1_view2')
        res['domain'] = [('res_model', '=', 'internal.memo.custom'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'internal.memo.custom', 'default_res_id': self.id}
        return res'''

    @api.multi
    def button_refund_customer(self): #vis_post
        self.ensure_one()
        self.write({'state':'done'})
        xxxb = self.env['account.move'].search([('ref', '=', self.origin_ref)])
        if not xxxb:
            raise except_orm(_('Error'),_('There is no related journal bills for this Memo'))
        respx = {'type':'ir.actions.act_window',
                'name':_('Supplier Referene'),
                'res_model':'account.move',
                'view_type':'form',
                'view_mode':'form',
                'target':'current',
                'res_id':xxxb.id
                }
        #res = self.env['ir.actions.act_window'].for_xml_id('allocation', 'view_payment_action')
        return respx



    @api.multi
    def button_dla_pay(self): #vis_post
        self.ensure_one()
        #self.write({'state':'done'})
        '''res = self.env['ir.actions.act_window'].for_xml_id('account', 'action_account_payments_payable')
        return res '''
        user = self.env.user
        account = user.company_id
        journal = account.bank_journal_ids.id

        respx = {'type':'ir.actions.act_window',
                'name':_('Direct Labour Payment'),
                'res_model':'account.payment',
                'view_type':'form',
                'view_mode':'form',
                'target':'new',
                'context':{
                            'default_amount':self.amountfig,
                            'default_communication':self.origin_ref,
                            'default_payment_type': 'outbound' or 'inbound',
                            'default_partner_id':self.vendor_bill.partner_id.id,
                            #'default_journal_id':journal
                            }

                }
        self.write({'state':'done'})

        #res = self.env['ir.actions.act_window'].for_xml_id('allocation', 'view_payment_action')
        return respx






class Send_Message(models.Model):
    _name="send.memo.message"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    #_inherit='res.users'
    reason = fields.Char('Reason')#<tree string="Memo Payments" colors="red:state == 'account';black:state == 'manager';green:state == 'coo';grey:state == 'refused';">

    date = fields.Datetime('Date')
    resp=fields.Many2one('res.users','Responsible')#, default=self.write_uid.id)
    memo_record = fields.Many2one('internal.memo.custom','Memo ID')

    def _change_state(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        all_records = self.env['internal.memo.custom'].browse(active_ids)
        state = all_records.write({'state':'refused'})
        return state
    def _send_message(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', [])
        all_records = self.env['internal.memo.custom'].browse(active_ids)
        #message = all_records.write({'state':'refused'})
        #return state

    @api.multi
    def post_refuse(self):
        get_state = self.env['internal.memo.custom'].search([('id','=', self.memo_record.id)])
        reasons = "%s Refused the Memo because of the following reason: \n %s." %(self.env.user.name,self.reason)
        get_state.write({'description_two':reasons})
        get_state.message_posts()
        self._change_state()
        return{'type': 'ir.actions.act_window_close'}


class Send_Request(models.Model):
    _name="send.memo.request"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    name = fields.Char('Memo Request Description')
    date = fields.Datetime(string='Date',default=fields.Date.context_today, required=True, copy=False)
    employee_id = fields.Many2one('hr.employee', string = 'Employee', default =_default_employee)
    dept_ids = fields.Char(string ='Department', related='employee_id.department_id.name',readonly = True, store =True)
    description = fields.Char('Note')
    project_id = fields.Many2one('account.analytic.account', 'Project')
    amountfig = fields.Float('Budget Amount', store=True)
    description_two=fields.Text('Reasons')
    file_upload = fields.Binary('File Upload')
    state = fields.Selection([('submit', 'Draft'),
                                ('headunit', 'HOU'),
                                ('manager', 'GM'),

                                ('ed', 'ED'),
                                ('coo', 'MD/CEO'),

                                ('post', 'Posted'),

                                ('approved', 'Approved'),
                                ('refused', 'Refused')
                              ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='submit', required=True,
        help='Request Report State')
    users_followers = fields.Many2many('hr.employee', string='Add followers')

    invoice_ref = fields.Many2one('account.invoice', 'Invoice Ref')


    @api.multi
    def unlink(self):
        for holiday in self.filtered(lambda holiday: holiday.state not in ['submit', 'refused', 'post']):
            raise ValidationError(_('You cannot delete a Memo which is in %s state.') % (holiday.state,))
        return super(Send_Request, self).unlink()


    @api.model
    def _needaction_domain_get(self):

        if self.env.user == "Administrator":
            return False
        return [('state', 'in', ['headunit','manager','ed','coo','post'])]



    @api.onchange('invoice_ref')
    def get_invoice_total(self):

        for order in self:
            invoice_amount = self.env['account.invoice'].search([('id', '=', order.invoice_ref.id)])

            if invoice_amount:
                order.amountfig = invoice_amount.amount_total

    def mail_sending(self, email_from, email_to, bodyx):

        from_browse =self.env.user.name

        for order in self:
            partner_mails = order.users_followers
            mail_append=[]
            for partner_emails in partner_mails:

                mail_append.append(partner_emails.work_email)

            subject = "Memo Request Notification"
            #body = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} is requested on the date of {}</br> </br>Thanks".format(self.employee_id.name,self.date)
            email_froms = str(from_browse) + " <"+str(email_from)+">"

            mail_appends = (', '.join(str(item)for item in mail_append))

            mail_data={
                'email_from': email_froms,
                'subject':subject,
                'email_to':email_to,
                'email_cc':mail_appends,
                'reply_to': email_from,
                'body_html':bodyx
                }
            mail_id =  order.env['mail.mail'].create(mail_data)
            order.env['mail.mail'].send(mail_id)



    def send_to_manager(self):
        self.write({'state':'headunit'})
        body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)


        email_from = self.env.user.email
        email_to = self.employee_id.work_email
        bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been sent to HOU </br> </br>Thanks".format(self.employee_id.name)

        self.mail_sending(email_from,email_to,bodyx)




    def send_headunit_to_Gmanager(self):
        self.write({'state':'manager'})
        body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

        email_from = self.env.user.email
        email_to = self.employee_id.work_email

        bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been sent to Manager for approval </br> </br>Thanks".format(self.employee_id.name)

        self.mail_sending(email_from,email_to,bodyx)




    def send_Gmanager_ed_coo(self):
        one_million = float(1000000)

        if self.amountfig  <= one_million:
            self.write({'state':'ed'})
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

            email_from = self.env.user.email
            email_to = self.employee_id.work_email
            bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been sent to ED for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)



        elif self.amountfig >= one_million:
            self.write({'state':'coo'})
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)
            email_from = self.env.user.email
            email_to = self.employee_id.work_email


            bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been sent to CEO for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)


        else:
            email_from = self.env.user.email
            email_to = self.employee_id.work_email

            bodyx = "Dear Sir/Madam, </br>We wish to notify that the memo from {} has been sent back simply because an amount was not specified for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)

            self.write({'state':'submit'})

    def send_Gmanager_ed_coo_submit(self):
        one_million = float(1000000)
        if self.amountfig  <= one_million:
            self.write({'state':'ed'})
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

            email_from = self.env.user.email
            email_to = self.employee_id.work_email
            bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been sent to ED for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)

        elif self.amountfig >= one_million:
            self.write({'state':'coo'})
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)
            email_from = self.env.user.email
            email_to = self.employee_id.work_email


            bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been sent to CEO for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)


        else:
            email_from = self.env.user.email
            email_to = self.employee_id.work_email

            bodyx = "Dear Sir/Madam, </br>We wish to notify that the memo from {} has been sent back simply because an amount was not specified for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)

            self.write({'state':'manager'})


    def send_ed_to_coo(self):
        one_million = float(1000000)
        if self.amountfig  <= one_million:
            self.write({'state':'approved'})
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

            email_from = self.env.user.email
            email_to = self.employee_id.work_email

            bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been approval for procurement</br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)



        elif self.amountfig >= one_million:
            self.write({'state':'coo'})
            body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
            records = self._get_followers()
            followers = records
            self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)
            email_from = self.env.user.email
            email_to = self.employee_id.work_email

            bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been sent to CEO for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)

        else:
            email_from = self.env.user.email
            email_to = self.employee_id.work_email

            bodyx = "Dear Sir/Madam, </br>We wish to notify that the memo from {} has been sent back simply because an amount was not specified for approval </br> </br>Thanks".format(self.employee_id.name)

            self.mail_sending(email_from,email_to,bodyx)

            self.write({'state':'submit'})

            #raise ValidationError('No amount on the requested memo')

    def send_coo_to_approve(self):
        self.write({'state':'approved'})
        body = "The Memo has been submitted to CEO for Approval on %s" % (datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

        email_from = self.env.user.email
        email_to = self.employee_id.work_email
        bodyx = "Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been approval </br> </br>Thanks".format(self.employee_id.name)

        self.mail_sending(email_from,email_to,bodyx)




    @api.multi
    def submit_manager(self):
        return self.send_to_manager()

    @api.multi
    def submitHouManager(self):
        return self.send_headunit_to_Gmanager()
    @api.multi
    def submitGmEdCoo(self):
        return self.send_Gmanager_ed_coo()
    @api.multi
    def submitEdCoo(self):
        return self.send_ed_to_coo()
    @api.multi
    def submitCooApp(self):
        return self.send_coo_to_approve()
    @api.multi
    def approval(self):
        ret = {'type':'ir.actions.act_window',
                'name':_('Procure item'),
                'res_model':'account.invoice',
                'view_type':'form',
                'view_mode':'form',
                'target':'new',
                #'context':{
                            #'default_memo_id':self.id,
                            #'default_communication':self.origin_ref,
                            #'default_payment_type': 'outbound' or 'inbound',
                            #'default_partner_id':self.vendor_bill.partner_id.id,
                            #'default_journal_id':journal
                            #}

                }

        #self.write({'state':'done'})
        return ret

    @api.multi
    def refused(self):
        self.write({'state':'refused'})
        body ="The Memo has been rejected by %s on %s" % (self.env.user.name,datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)




    @api.multi
    def refuse_hou(self):
        self.write({'state':'refused'})

        body ="The Memo has been rejected by %s on %s" % (self.env.user.name,datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

        email_from = self.env.user.email
        email_to = self.employee_id.work_email
        bodyx = self.description#"Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been approval </br> </br>Thanks".format(self.employee_id.name)

        self.mail_sending(email_from,email_to,bodyx)

    @api.multi
    def refuse_gm(self):
        self.write({'state':'refused'})

        body ="The Memo has been rejected by %s on %s" % (self.env.user.name,datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

        email_from = self.env.user.email
        email_to = self.employee_id.work_email
        bodyx = self.description#"Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been approval </br> </br>Thanks".format(self.employee_id.name)

        self.mail_sending(email_from,email_to,bodyx)

    @api.multi
    def refuse_ed(self):
        self.write({'state':'refused'})

        body ="The Memo has been rejected by %s on %s" % (self.env.user.name,datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

        email_from = self.env.user.email
        email_to = self.employee_id.work_email
        bodyx = self.description#"Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been approval </br> </br>Thanks".format(self.employee_id.name)

        self.mail_sending(email_from,email_to,bodyx)


    @api.multi
    def refuse_coo(self):
        self.write({'state':'refused'})

        body ="The Memo has been rejected by %s on %s" % (self.env.user.name,datetime.strftime(datetime.today(), '%d-%m-%y'))
        records = self._get_followers()
        followers = records
        self.message_post(body=body, subtype='mt_comment',message_type='notification',partner_ids=followers)

        email_from = self.env.user.email
        email_to = self.employee_id.work_email
        bodyx = self.description#"Dear Sir/Madam, </br>We wish to notify you that a memo from {} has been approval </br> </br>Thanks".format(self.employee_id.name)

        self.mail_sending(email_from,email_to,bodyx)









    @api.multi
    def set_draft(self):
        self.write({'state':'submit'})


'''class Purchase_Order(models.Model):
    _inherit = "purchase.order"

    memo_id = fields.Integer('Memo ID')
    @api.multi
    def button_confirm(self):
        search_memo = self.env['send.memo.request'].search([('id', '=', self.memo_id)])
        memo_state = search_memo.state
        memo_state = "post"

        for order in self:
            if order.state not in ['draft', 'sent']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True


        '''

















