# This file defines command line commands for manage.py
#
# Copyright 2014 SolidBuilds.com. All rights reserved
#
# Authors: Ling Thio <ling.thio@gmail.com>

import datetime

from app.models.user_models import User, Role, Tokens
from flask import current_app
from flask_script import Command

from app import db


class InitDbCommand(Command):
    """ Initialize the database."""

    def run(self):
        init_db()
        print('Database has been initialized.')

def init_db():
    """ Initialize the database."""
    db.drop_all()
    db.create_all()
    create_users()
    create_customers()
    create_prompts()
    create_tokens()


def create_users():
    """ Create users """

    # Create all tables
    db.create_all()

    # Adding roles
    admin_role = find_or_create_role('admin', u'Admin')

    # Add users
    user = find_or_create_user(u'Admin', u'Example', u'admin@example.com', 'Password1', admin_role)
    user = find_or_create_user(u'Member', u'Example', u'member@example.com', 'Password1')
    user = find_or_create_user(u'Fred', u'Zimmerman', u'admin@nimblebooks.com', 'Hamburger12', admin_role)

    # Save to DB
    db.session.commit()

def create_presets():
    db.create_all()

    preset = find_or_create_preset('1', True, u'Test', u'Test')

    db.session.commit()

def create_tokens():
    db.create_all()
    created_on = datetime.datetime.utcnow()
    tokens = find_or_create_tokens('1', 1, 100, created_on)

    db.session.commit()

def create_customers():
    """ Create customers """
    db.create_all()
    db.session.commit()


def find_or_create_role(name, label):
    """ Find existing role or create new role """
    role = Role.query.filter(Role.name == name).first()
    if not role:
        role = Role(name=name, label=label)
        db.session.add(role)
    return role


def find_or_create_user(first_name, last_name, email, password, role=None):
    """ Find existing user or create new user """
    user = User.query.filter(User.email == email).first()
    if not user:
        user = User(email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=current_app.user_manager.password_manager.hash_password(password),
                    active=True,
                    email_confirmed_at=datetime.datetime.utcnow())
        if role:
            user.roles.append(role)
        db.session.add(user)
    return user

def find_or_create_customer(id, user_id, stripeCustomerId, stripeSubscriptionId):
    """ Find existing customer or create new customer """
    customer = Customer.query.filter(Customer.stripeCustomerId == stripeCustomerId).first()
    if not customer:
        customer = Customer(id=id,
        user_id=user_id,
        stripeCustomerId=stripeCustomerId,
        stripeSubscriptionId=stripeSubscriptionId)
        db.session.add(customer)
    return customer

def find_or_create_preset(id, active, preset_name, preset_author):
    """ Find existing customer or create new preset """
    preset = Prompt.query.filter(Prompt.preset_name == preset_name).first()
    if not preset:
        preset = Prompt(id=id,
        active=active,
        preset_name=preset_name,
        preset_author=preset_author)
        db.session.add(preset)
    return preset

def find_or_create_tokens(id, user_id, totaltokens, created_on):
    """ Find existing customer or create new prompt """
    tokens = Tokens.query.filter(Tokens.user_id == user_id).first()
    if not tokens:
        tokens = Tokens(id=id,
        user_id=user_id,
        totaltokens=totaltokens,
        created_on=created_on)
        db.session.add(tokens)
    return tokens


