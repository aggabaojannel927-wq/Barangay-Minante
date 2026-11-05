-- Fresh application schema only; no INSERT statements or personal data.
PRAGMA foreign_keys=ON;
BEGIN TRANSACTION;
CREATE TABLE accepted_id_types (
	id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	description TEXT, 
	is_active BOOLEAN NOT NULL, 
	is_accepted_for_registration BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE activity_logs (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	actor_role VARCHAR(20), 
	action VARCHAR(120) NOT NULL, 
	resource VARCHAR(50) NOT NULL, 
	target_reference VARCHAR(80), 
	details TEXT, 
	ip_address VARCHAR(50), 
	user_agent VARCHAR(255), 
	timestamp DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE announcements (
	id INTEGER NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	body TEXT NOT NULL, 
	category VARCHAR(60) NOT NULL, 
	publish_start_at DATETIME, 
	expired_at DATETIME, 
	program_id INTEGER, 
	is_published BOOLEAN NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	approved_by INTEGER, 
	approved_at DATETIME, 
	published_at DATETIME NOT NULL, 
	expires_at DATETIME, 
	created_by INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(program_id) REFERENCES community_programs (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE application_requirements (
	id INTEGER NOT NULL, 
	application_id INTEGER NOT NULL, 
	definition_id INTEGER NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	requirement_type VARCHAR(30) NOT NULL, 
	instructions TEXT, 
	is_required BOOLEAN NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	value TEXT, 
	file_path VARCHAR(255), 
	submitted_at DATETIME, 
	reviewed_by INTEGER, 
	reviewed_at DATETIME, 
	review_note TEXT, 
	PRIMARY KEY (id), 
	UNIQUE (application_id, definition_id), 
	FOREIGN KEY(application_id) REFERENCES permit_applications (id), 
	FOREIGN KEY(definition_id) REFERENCES service_requirements (id), 
	FOREIGN KEY(reviewed_by) REFERENCES users (id)
);
CREATE TABLE assistance_referrals (
	id INTEGER NOT NULL, 
	reference_no VARCHAR(40) NOT NULL, 
	resident_id INTEGER NOT NULL, 
	category VARCHAR(120) NOT NULL, 
	description TEXT NOT NULL, 
	assigned_to INTEGER, 
	status VARCHAR(30) NOT NULL, 
	sensitivity_level VARCHAR(20) NOT NULL, 
	created_by INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (reference_no), 
	FOREIGN KEY(resident_id) REFERENCES users (id), 
	FOREIGN KEY(assigned_to) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE blotter_cases (
	id INTEGER NOT NULL, 
	case_no VARCHAR(40) NOT NULL, 
	complainant_id INTEGER NOT NULL, 
	respondent_name VARCHAR(150) NOT NULL, 
	respondent_address VARCHAR(255), 
	incident_type VARCHAR(120) NOT NULL, 
	incident_date DATETIME NOT NULL, 
	incident_location VARCHAR(255) NOT NULL, 
	narrative TEXT NOT NULL, 
	supporting_document_path VARCHAR(255), 
	status VARCHAR(30) NOT NULL, 
	filed_date DATETIME, 
	assigned_officer VARCHAR(150), 
	resolution TEXT, 
	hearing_date DATETIME, 
	updated_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (case_no), 
	FOREIGN KEY(complainant_id) REFERENCES users (id), 
	FOREIGN KEY(updated_by) REFERENCES users (id)
);
CREATE TABLE community_programs (
	id INTEGER NOT NULL, 
	program_type VARCHAR(30) NOT NULL, 
	title VARCHAR(180) NOT NULL, 
	description TEXT NOT NULL, 
	provider VARCHAR(180), 
	assistance_type VARCHAR(120), 
	eligibility TEXT NOT NULL, 
	target_categories TEXT, 
	instructions TEXT, 
	requirements_json TEXT NOT NULL, 
	application_start DATETIME NOT NULL, 
	application_deadline DATETIME NOT NULL, 
	distribution_date DATETIME, 
	slots INTEGER, 
	claim_rule VARCHAR(30) NOT NULL, 
	applications_enabled BOOLEAN NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	created_by INTEGER NOT NULL, 
	approved_by INTEGER, 
	published_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (program_type IN ('Scholarship', 'Ayuda')), 
	CHECK (status IN ('Draft', 'Published', 'Closed')), 
	CHECK (application_deadline > application_start), 
	CHECK (claim_rule IN ('Per Resident', 'Per Household', 'Repeatable')), 
	CHECK (slots IS NULL OR slots > 0), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(approved_by) REFERENCES users (id)
);
CREATE TABLE event_categories (
	id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	description TEXT, 
	fee NUMERIC(10, 2), 
	fee_is_configured BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE event_requests (
	id INTEGER NOT NULL, 
	reference_no VARCHAR(40) NOT NULL, 
	requester_id INTEGER NOT NULL, 
	event_name VARCHAR(180) NOT NULL, 
	category_id INTEGER, 
	venue_id INTEGER, 
	event_type VARCHAR(120) NOT NULL, 
	description TEXT NOT NULL, 
	proposed_date DATE NOT NULL, 
	proposed_start_time TIME, 
	proposed_end_time TIME, 
	proposed_location VARCHAR(255) NOT NULL, 
	expected_attendees INTEGER NOT NULL, 
	supporting_document_path VARCHAR(255), 
	fee_at_submission NUMERIC(10, 2) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	reviewed_by INTEGER, 
	decision_date DATETIME, 
	remarks TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (reference_no), 
	FOREIGN KEY(requester_id) REFERENCES users (id), 
	FOREIGN KEY(category_id) REFERENCES event_categories (id), 
	FOREIGN KEY(venue_id) REFERENCES event_venues (id), 
	FOREIGN KEY(reviewed_by) REFERENCES users (id)
);
CREATE TABLE event_reservations (
	id INTEGER NOT NULL, 
	venue_id INTEGER NOT NULL, 
	event_request_id INTEGER, 
	requester_id INTEGER NOT NULL, 
	starts_at DATETIME NOT NULL, 
	ends_at DATETIME NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	hold_token_hash VARCHAR(64), 
	hold_expires_at DATETIME, 
	draft_payload TEXT, 
	released_at DATETIME, 
	release_reason VARCHAR(255), 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(venue_id) REFERENCES event_venues (id), 
	FOREIGN KEY(event_request_id) REFERENCES event_requests (id) ON DELETE CASCADE, 
	FOREIGN KEY(requester_id) REFERENCES users (id)
);
CREATE TABLE event_venues (
	id INTEGER NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	address VARCHAR(255), 
	description TEXT, 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE general_concerns (
	id INTEGER NOT NULL, 
	reference_no VARCHAR(40) NOT NULL, 
	resident_id INTEGER NOT NULL, 
	category VARCHAR(120) NOT NULL, 
	description TEXT NOT NULL, 
	location VARCHAR(255), 
	sensitivity_level VARCHAR(20) NOT NULL, 
	assigned_to INTEGER, 
	status VARCHAR(30) NOT NULL, 
	encoded_by INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (reference_no), 
	FOREIGN KEY(resident_id) REFERENCES users (id), 
	FOREIGN KEY(assigned_to) REFERENCES users (id), 
	FOREIGN KEY(encoded_by) REFERENCES users (id)
);
CREATE TABLE household_members (
	id INTEGER NOT NULL, 
	household_id INTEGER NOT NULL, 
	resident_id INTEGER NOT NULL, 
	membership_status VARCHAR(20) NOT NULL, 
	joined_at DATETIME NOT NULL, 
	left_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (household_id, resident_id), 
	FOREIGN KEY(household_id) REFERENCES households (id), 
	FOREIGN KEY(resident_id) REFERENCES users (id)
);
CREATE TABLE households (
	id INTEGER NOT NULL, 
	household_number VARCHAR(80) NOT NULL, 
	address VARCHAR(255), 
	head_resident_id INTEGER, 
	status VARCHAR(20) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(head_resident_id) REFERENCES users (id)
);
CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	user_id INTEGER, 
	recipient_user_id INTEGER, 
	recipient_contact VARCHAR(150), 
	title VARCHAR(180) NOT NULL, 
	message TEXT NOT NULL, 
	channel VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	related_type VARCHAR(30), 
	related_id INTEGER, 
	sent_at DATETIME, 
	read_at DATETIME, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(recipient_user_id) REFERENCES users (id)
);
CREATE TABLE password_reset_tokens (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	used_at DATETIME, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);
CREATE TABLE payment_authorities (
	user_id INTEGER NOT NULL, 
	granted_by INTEGER NOT NULL, 
	PRIMARY KEY (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(granted_by) REFERENCES users (id)
);
CREATE TABLE payments (
	id INTEGER NOT NULL, 
	payment_reference VARCHAR(40) NOT NULL, 
	permit_id INTEGER, 
	event_id INTEGER, 
	resident_id INTEGER NOT NULL, 
	fee_snapshot NUMERIC(10, 2) NOT NULL, 
	amount_paid NUMERIC(10, 2) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	payment_method VARCHAR(60), 
	recorded_by INTEGER NOT NULL, 
	paid_at DATETIME NOT NULL, 
	notes TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CHECK ((permit_id IS NOT NULL AND event_id IS NULL) OR (event_id IS NOT NULL AND permit_id IS NULL)), 
	CHECK (status IN ('Paid', 'Waived')), 
	CHECK (fee_snapshot > 0 AND ((status = 'Paid' AND amount_paid = fee_snapshot) OR (status = 'Waived' AND amount_paid = 0))), 
	UNIQUE (payment_reference), 
	UNIQUE (permit_id), 
	FOREIGN KEY(permit_id) REFERENCES permit_applications (id), 
	UNIQUE (event_id), 
	FOREIGN KEY(event_id) REFERENCES event_requests (id), 
	FOREIGN KEY(resident_id) REFERENCES users (id), 
	FOREIGN KEY(recorded_by) REFERENCES users (id)
);
CREATE TABLE permit_applications (
	id INTEGER NOT NULL, 
	reference_no VARCHAR(40) NOT NULL, 
	applicant_id INTEGER NOT NULL, 
	permit_type_id INTEGER NOT NULL, 
	purpose TEXT NOT NULL, 
	fee_at_submission NUMERIC(10, 2) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	application_date DATETIME, 
	appointment_date DATETIME, 
	decision_date DATETIME, 
	decided_by INTEGER, 
	reviewed_by INTEGER, 
	remarks TEXT, 
	permit_file_path VARCHAR(255), 
	attachment_path VARCHAR(255), 
	request_source VARCHAR(30) NOT NULL, 
	encoded_by_staff_id INTEGER, 
	office_name VARCHAR(150), 
	endorsed_by INTEGER, 
	endorsed_at DATETIME, 
	endorsement_note TEXT, 
	signed_by INTEGER, 
	signed_at DATETIME, 
	signatory_name VARCHAR(150), 
	signatory_title VARCHAR(150), 
	signature_path VARCHAR(255), 
	document_version INTEGER NOT NULL, 
	payment_confirmed_at DATETIME, 
	payment_confirmed_by INTEGER, 
	payment_reference VARCHAR(120), 
	released_by INTEGER, 
	released_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (reference_no), 
	FOREIGN KEY(applicant_id) REFERENCES users (id), 
	FOREIGN KEY(permit_type_id) REFERENCES permit_types (id), 
	FOREIGN KEY(decided_by) REFERENCES users (id), 
	FOREIGN KEY(reviewed_by) REFERENCES users (id), 
	FOREIGN KEY(encoded_by_staff_id) REFERENCES users (id), 
	FOREIGN KEY(endorsed_by) REFERENCES users (id), 
	FOREIGN KEY(signed_by) REFERENCES users (id), 
	FOREIGN KEY(payment_confirmed_by) REFERENCES users (id), 
	FOREIGN KEY(released_by) REFERENCES users (id)
);
CREATE TABLE permit_signatories (
	id INTEGER NOT NULL, 
	permit_type_id INTEGER NOT NULL, 
	authorized_admin_id INTEGER NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	title VARCHAR(150) NOT NULL, 
	file_path VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (permit_type_id), 
	FOREIGN KEY(permit_type_id) REFERENCES permit_types (id), 
	FOREIGN KEY(authorized_admin_id) REFERENCES users (id)
);
CREATE TABLE permit_types (
	id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	description TEXT, 
	requirements TEXT, 
	processing_time VARCHAR(180), 
	fee NUMERIC(10, 2), 
	fee_is_configured BOOLEAN NOT NULL, 
	validity_days INTEGER, 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE program_application_history (
	id INTEGER NOT NULL, 
	application_id INTEGER NOT NULL, 
	actor_id INTEGER NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	requirements_json TEXT NOT NULL, 
	note TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(application_id) REFERENCES program_applications (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);
CREATE TABLE program_applications (
	id INTEGER NOT NULL, 
	reference_no VARCHAR(40) NOT NULL, 
	program_id INTEGER NOT NULL, 
	resident_id INTEGER NOT NULL, 
	household_id INTEGER, 
	claim_key VARCHAR(80), 
	status VARCHAR(30) NOT NULL, 
	requirements_json TEXT NOT NULL, 
	encoded_by INTEGER NOT NULL, 
	reviewed_by INTEGER, 
	reviewed_at DATETIME, 
	released_by INTEGER, 
	released_at DATETIME, 
	review_note TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (program_id, claim_key), 
	CHECK (status IN ('Submitted', 'Under Review', 'Needs Requirements', 'Qualified', 'Not Qualified', 'Approved', 'Waitlisted', 'Completed')), 
	UNIQUE (reference_no), 
	FOREIGN KEY(program_id) REFERENCES community_programs (id), 
	FOREIGN KEY(resident_id) REFERENCES users (id), 
	FOREIGN KEY(household_id) REFERENCES households (id), 
	FOREIGN KEY(encoded_by) REFERENCES users (id), 
	FOREIGN KEY(reviewed_by) REFERENCES users (id), 
	FOREIGN KEY(released_by) REFERENCES users (id)
);
CREATE TABLE queue_entries (
	id INTEGER NOT NULL, 
	queue_date DATE NOT NULL, 
	queue_number VARCHAR(30) NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	related_type VARCHAR(20), 
	related_id INTEGER, 
	resident_id INTEGER NOT NULL, 
	permit_application_id INTEGER, 
	status VARCHAR(20) NOT NULL, 
	priority_category VARCHAR(80), 
	called_at DATETIME, 
	served_at DATETIME, 
	completed_at DATETIME, 
	created_by INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (queue_date, queue_number), 
	FOREIGN KEY(resident_id) REFERENCES users (id), 
	FOREIGN KEY(permit_application_id) REFERENCES permit_applications (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE reports (
	id INTEGER NOT NULL, 
	generated_by INTEGER NOT NULL, 
	report_type VARCHAR(50) NOT NULL, 
	format VARCHAR(10) NOT NULL, 
	filters_json TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(generated_by) REFERENCES users (id)
);
CREATE TABLE request_assignments (
	id INTEGER NOT NULL, 
	permit_application_id INTEGER NOT NULL, 
	assigned_to_user_id INTEGER NOT NULL, 
	assigned_by INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	note TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(permit_application_id) REFERENCES permit_applications (id), 
	FOREIGN KEY(assigned_to_user_id) REFERENCES users (id), 
	FOREIGN KEY(assigned_by) REFERENCES users (id)
);
CREATE TABLE requirement_history (
	id INTEGER NOT NULL, 
	requirement_id INTEGER NOT NULL, 
	actor_id INTEGER NOT NULL, 
	actor_role VARCHAR(20) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	note TEXT, 
	file_path VARCHAR(255), 
	value TEXT, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(requirement_id) REFERENCES application_requirements (id), 
	FOREIGN KEY(actor_id) REFERENCES users (id)
);
CREATE TABLE resident_family_members (
	id INTEGER NOT NULL, 
	head_profile_id INTEGER NOT NULL, 
	household_id INTEGER, 
	full_name VARCHAR(150) NOT NULL, 
	age INTEGER, 
	gender VARCHAR(6), 
	date_of_birth DATE, 
	relationship VARCHAR(80), 
	member_key VARCHAR(64) NOT NULL, 
	created_by INTEGER NOT NULL, 
	updated_by INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (head_profile_id, member_key), 
	CHECK (age >= 0 AND age <= 120), 
	CHECK (gender IN ('Male', 'Female')), 
	FOREIGN KEY(head_profile_id) REFERENCES resident_profiles (id), 
	FOREIGN KEY(household_id) REFERENCES households (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(updated_by) REFERENCES users (id)
);
CREATE TABLE resident_feedback (
	id INTEGER NOT NULL, 
	resident_id INTEGER NOT NULL, 
	permit_application_id INTEGER NOT NULL, 
	rating INTEGER NOT NULL, 
	comment TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (resident_id, permit_application_id), 
	FOREIGN KEY(resident_id) REFERENCES users (id), 
	FOREIGN KEY(permit_application_id) REFERENCES permit_applications (id)
);
CREATE TABLE resident_profiles (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	date_of_birth DATE, 
	sex VARCHAR(40), 
	civil_status VARCHAR(40), 
	house_number_street VARCHAR(180), 
	purok_zone VARCHAR(120), 
	resident_type_id INTEGER, 
	resident_type_other VARCHAR(150), 
	residency_status VARCHAR(40), 
	years_of_residency INTEGER, 
	occupation VARCHAR(150), 
	is_household_head BOOLEAN NOT NULL, 
	has_disability BOOLEAN, 
	disability_declined BOOLEAN NOT NULL, 
	disability_type VARCHAR(50), 
	disability_other VARCHAR(300), 
	household_number VARCHAR(80), 
	emergency_contact_name VARCHAR(150), 
	emergency_contact_relationship VARCHAR(80), 
	emergency_contact_number VARCHAR(20), 
	accepted_id_type_id INTEGER, 
	valid_id_number VARCHAR(120), 
	valid_id_type_other VARCHAR(150), 
	valid_id_file_path VARCHAR(255), 
	id_verification_status VARCHAR(30) NOT NULL, 
	id_verified_by INTEGER, 
	id_verified_at DATETIME, 
	id_rejection_reason TEXT, 
	address_verification_status VARCHAR(30) NOT NULL, 
	address_verified_by INTEGER, 
	address_verified_at DATETIME, 
	address_rejection_reason TEXT, 
	privacy_consent BOOLEAN NOT NULL, 
	privacy_consented_at DATETIME, 
	approval_status VARCHAR(20) NOT NULL, 
	approval_remarks TEXT, 
	reviewed_by INTEGER, 
	reviewed_at DATETIME, 
	approval_notice_seen_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(resident_type_id) REFERENCES resident_types (id), 
	FOREIGN KEY(accepted_id_type_id) REFERENCES accepted_id_types (id), 
	FOREIGN KEY(id_verified_by) REFERENCES users (id), 
	FOREIGN KEY(address_verified_by) REFERENCES users (id), 
	FOREIGN KEY(reviewed_by) REFERENCES users (id)
);
CREATE TABLE resident_types (
	id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	description TEXT, 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
CREATE TABLE resident_update_requests (
	id INTEGER NOT NULL, 
	resident_id INTEGER NOT NULL, 
	field_name VARCHAR(80) NOT NULL, 
	old_value TEXT, 
	proposed_value TEXT NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	reviewed_by INTEGER, 
	reviewed_at DATETIME, 
	created_by INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(resident_id) REFERENCES users (id), 
	FOREIGN KEY(reviewed_by) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);
CREATE TABLE schedules (
	id INTEGER NOT NULL, 
	reference_no VARCHAR(40) NOT NULL, 
	related_type VARCHAR(20) NOT NULL, 
	related_id INTEGER NOT NULL, 
	requested_by INTEGER NOT NULL, 
	scheduled_datetime DATETIME NOT NULL, 
	purpose VARCHAR(255) NOT NULL, 
	note TEXT, 
	status VARCHAR(30) NOT NULL, 
	confirmed_by INTEGER, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (reference_no), 
	FOREIGN KEY(requested_by) REFERENCES users (id), 
	FOREIGN KEY(confirmed_by) REFERENCES users (id)
);
CREATE TABLE service_requirements (
	id INTEGER NOT NULL, 
	permit_type_id INTEGER NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	requirement_type VARCHAR(30) NOT NULL, 
	instructions TEXT, 
	is_required BOOLEAN NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	position INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (permit_type_id, name), 
	FOREIGN KEY(permit_type_id) REFERENCES permit_types (id)
);
CREATE TABLE system_settings (
	id INTEGER NOT NULL, 
	"key" VARCHAR(100) NOT NULL, 
	value TEXT, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE ("key")
);
CREATE TABLE users (
	id INTEGER NOT NULL, 
	username VARCHAR(80) NOT NULL, 
	online_access_enabled BOOLEAN NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	full_name VARCHAR(150) NOT NULL, 
	contact_number VARCHAR(20), 
	email VARCHAR(150), 
	address VARCHAR(255), 
	is_active BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);
CREATE INDEX ix_accepted_id_types_is_accepted_for_registration ON accepted_id_types (is_accepted_for_registration);
CREATE INDEX ix_accepted_id_types_is_active ON accepted_id_types (is_active);
CREATE INDEX ix_activity_logs_action ON activity_logs (action);
CREATE INDEX ix_activity_logs_resource ON activity_logs (resource);
CREATE INDEX ix_activity_logs_timestamp ON activity_logs (timestamp);
CREATE INDEX ix_activity_logs_user_id ON activity_logs (user_id);
CREATE INDEX ix_announcements_created_by ON announcements (created_by);
CREATE INDEX ix_announcements_is_published ON announcements (is_published);
CREATE INDEX ix_announcements_publish_start_at ON announcements (publish_start_at);
CREATE INDEX ix_announcements_published_at ON announcements (published_at);
CREATE INDEX ix_announcements_status ON announcements (status);
CREATE INDEX ix_application_requirements_application_id ON application_requirements (application_id);
CREATE INDEX ix_application_requirements_reviewed_by ON application_requirements (reviewed_by);
CREATE INDEX ix_application_requirements_status ON application_requirements (status);
CREATE INDEX ix_assistance_referrals_resident_id ON assistance_referrals (resident_id);
CREATE INDEX ix_assistance_referrals_status ON assistance_referrals (status);
CREATE INDEX ix_blotter_cases_complainant_id ON blotter_cases (complainant_id);
CREATE INDEX ix_blotter_cases_status ON blotter_cases (status);
CREATE INDEX ix_blotter_owner_filed ON blotter_cases (complainant_id, filed_date);
CREATE INDEX ix_community_programs_application_deadline ON community_programs (application_deadline);
CREATE INDEX ix_community_programs_application_start ON community_programs (application_start);
CREATE INDEX ix_community_programs_status ON community_programs (status);
CREATE INDEX ix_event_created ON event_requests (created_at);
CREATE INDEX ix_event_owner_created ON event_requests (requester_id, created_at);
CREATE INDEX ix_event_requests_requester_id ON event_requests (requester_id);
CREATE INDEX ix_event_requests_status ON event_requests (status);
CREATE INDEX ix_event_requests_venue_id ON event_requests (venue_id);
CREATE INDEX ix_event_reservation_status_expiry ON event_reservations (status, hold_expires_at);
CREATE INDEX ix_event_reservation_venue_interval ON event_reservations (venue_id, starts_at, ends_at);
CREATE UNIQUE INDEX ix_event_reservations_event_request_id ON event_reservations (event_request_id);
CREATE UNIQUE INDEX ix_event_reservations_hold_token_hash ON event_reservations (hold_token_hash);
CREATE INDEX ix_event_reservations_requester_id ON event_reservations (requester_id);
CREATE INDEX ix_event_reservations_status ON event_reservations (status);
CREATE INDEX ix_event_reservations_venue_id ON event_reservations (venue_id);
CREATE INDEX ix_event_venues_is_active ON event_venues (is_active);
CREATE INDEX ix_general_concerns_resident_id ON general_concerns (resident_id);
CREATE INDEX ix_general_concerns_sensitivity_level ON general_concerns (sensitivity_level);
CREATE INDEX ix_general_concerns_status ON general_concerns (status);
CREATE INDEX ix_household_members_household_id ON household_members (household_id);
CREATE INDEX ix_household_members_membership_status ON household_members (membership_status);
CREATE INDEX ix_household_members_resident_id ON household_members (resident_id);
CREATE UNIQUE INDEX ix_households_household_number ON households (household_number);
CREATE INDEX ix_households_status ON households (status);
CREATE INDEX ix_notification_owner_created ON notifications (user_id, created_at);
CREATE INDEX ix_notifications_channel ON notifications (channel);
CREATE INDEX ix_notifications_user_id ON notifications (user_id);
CREATE UNIQUE INDEX ix_password_reset_tokens_token_hash ON password_reset_tokens (token_hash);
CREATE INDEX ix_password_reset_tokens_user_id ON password_reset_tokens (user_id);
CREATE INDEX ix_payments_paid_at ON payments (paid_at);
CREATE INDEX ix_payments_resident_id ON payments (resident_id);
CREATE INDEX ix_permit_applications_applicant_id ON permit_applications (applicant_id);
CREATE INDEX ix_permit_applications_encoded_by_staff_id ON permit_applications (encoded_by_staff_id);
CREATE INDEX ix_permit_applications_endorsed_by ON permit_applications (endorsed_by);
CREATE INDEX ix_permit_applications_released_by ON permit_applications (released_by);
CREATE INDEX ix_permit_applications_request_source ON permit_applications (request_source);
CREATE INDEX ix_permit_applications_signed_by ON permit_applications (signed_by);
CREATE INDEX ix_permit_applications_status ON permit_applications (status);
CREATE INDEX ix_permit_created ON permit_applications (created_at);
CREATE INDEX ix_permit_owner_date ON permit_applications (applicant_id, application_date);
CREATE INDEX ix_program_application_created ON program_applications (program_id, created_at);
CREATE INDEX ix_program_application_history_application_id ON program_application_history (application_id);
CREATE INDEX ix_program_applications_program_id ON program_applications (program_id);
CREATE INDEX ix_program_applications_resident_id ON program_applications (resident_id);
CREATE INDEX ix_program_applications_status ON program_applications (status);
CREATE INDEX ix_queue_entries_permit_application_id ON queue_entries (permit_application_id);
CREATE INDEX ix_queue_entries_queue_date ON queue_entries (queue_date);
CREATE INDEX ix_queue_entries_resident_id ON queue_entries (resident_id);
CREATE INDEX ix_queue_entries_status ON queue_entries (status);
CREATE INDEX ix_request_assignments_assigned_to_user_id ON request_assignments (assigned_to_user_id);
CREATE INDEX ix_request_assignments_permit_application_id ON request_assignments (permit_application_id);
CREATE INDEX ix_request_assignments_status ON request_assignments (status);
CREATE INDEX ix_requirement_history_requirement_id ON requirement_history (requirement_id);
CREATE INDEX ix_resident_family_members_head_profile_id ON resident_family_members (head_profile_id);
CREATE INDEX ix_resident_family_members_household_id ON resident_family_members (household_id);
CREATE INDEX ix_resident_feedback_permit_application_id ON resident_feedback (permit_application_id);
CREATE INDEX ix_resident_feedback_resident_id ON resident_feedback (resident_id);
CREATE INDEX ix_resident_profiles_accepted_id_type_id ON resident_profiles (accepted_id_type_id);
CREATE INDEX ix_resident_profiles_address_verification_status ON resident_profiles (address_verification_status);
CREATE INDEX ix_resident_profiles_address_verified_by ON resident_profiles (address_verified_by);
CREATE INDEX ix_resident_profiles_approval_created ON resident_profiles (approval_status, created_at);
CREATE INDEX ix_resident_profiles_approval_status ON resident_profiles (approval_status);
CREATE INDEX ix_resident_profiles_id_verification_status ON resident_profiles (id_verification_status);
CREATE INDEX ix_resident_profiles_id_verified_by ON resident_profiles (id_verified_by);
CREATE INDEX ix_resident_profiles_residency_status ON resident_profiles (residency_status);
CREATE INDEX ix_resident_profiles_resident_type_id ON resident_profiles (resident_type_id);
CREATE INDEX ix_resident_profiles_reviewed_by ON resident_profiles (reviewed_by);
CREATE UNIQUE INDEX ix_resident_profiles_user_id ON resident_profiles (user_id);
CREATE INDEX ix_resident_types_is_active ON resident_types (is_active);
CREATE INDEX ix_resident_update_requests_resident_id ON resident_update_requests (resident_id);
CREATE INDEX ix_resident_update_requests_status ON resident_update_requests (status);
CREATE INDEX ix_schedules_related_id ON schedules (related_id);
CREATE INDEX ix_schedules_related_type ON schedules (related_type);
CREATE INDEX ix_schedules_scheduled_datetime ON schedules (scheduled_datetime);
CREATE INDEX ix_schedules_status ON schedules (status);
CREATE INDEX ix_service_requirements_is_active ON service_requirements (is_active);
CREATE INDEX ix_service_requirements_permit_type_id ON service_requirements (permit_type_id);
CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_role ON users (role);
CREATE UNIQUE INDEX ix_users_username ON users (username);
COMMIT;
