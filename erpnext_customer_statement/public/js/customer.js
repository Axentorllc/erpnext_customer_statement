
var _CUSTOMER_STATEMENT_SETTINGS = _CUSTOMER_STATEMENT_SETTINGS || {}

frappe.ui.form.on("Customer", "refresh", function (frm) {
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Erpnext Customer Statement Settings",
			name: "Erpnext Customer Statement Settings",
		},
		callback(r) {
			if (r.message) {

				_CUSTOMER_STATEMENT_SETTINGS = r.message;
				if (_CUSTOMER_STATEMENT_SETTINGS.enabled) {

					frm.add_custom_button(__("Customer Statement"), function () {
						// do something with these values, like an ajax request 
						// or call a server side frappe function using frappe.call

						var customer_statement_dialog = new frappe.ui.Dialog({
							title: __('Get Customer Statement'),
							fields: [
								{
									"label": "Company",
									"fieldname": "company",
									"fieldtype": "Link",
									"options": "Company",
									"reqd": 1,
									"default": frappe.defaults.get_default('company')
								},
								{
									"label": "From Date",
									"fieldname": "from_date",
									"fieldtype": "Date",
									"default": frappe.defaults.get_user_default("year_start_date")
								},
								{
									"label": "To Date",
									"fieldname": "to_date",
									"fieldtype": "Date",
									"default": frappe.datetime.nowdate()
								}
							],
							primary_action: function () {
								var values = customer_statement_dialog.get_values();
								var url = frappe.urllib.get_base_url() + '/api/method/erpnext_customer_statement.customer_statement.customer_statement.get_report_pdf?from_date=' + encodeURIComponent(values.from_date) + '&to_date=' + encodeURIComponent(values.to_date) + '&company=' + encodeURIComponent(values.company) + '&customer=' + encodeURIComponent(frm.doc.name)

								$.ajax({
									url: url,
									type: 'GET',
									success: function (result) {
										if (jQuery.isEmptyObject(result)) {
											frappe.msgprint('No Records for these settings.');
										}
										else {
											window.location = url;
										}
									}

								})
							},
							primary_action_label: __('Get Statement')
						});
						customer_statement_dialog.show();

					})
				}

			}
		}
	});
});

