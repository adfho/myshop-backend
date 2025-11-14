from marshmallow import Schema, fields, validate, validates, ValidationError

from routes.utils import validate_email, validate_password


class BaseSchema(Schema):
    class Meta:
        ordered = True


class RegisterSchema(BaseSchema):
    first_name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=120))
    email = fields.String(required=True)
    password = fields.String(required=True, load_only=True)

    @validates("email")
    def validate_email_field(self, value: str):
        if not validate_email(value):
            raise ValidationError("Invalid email format")

    @validates("password")
    def validate_password_field(self, value: str):
        if not validate_password(value):
            raise ValidationError(
                "Password must be at least 6 characters and contain letters and numbers"
            )


class LoginSchema(BaseSchema):
    email = fields.String(required=True)
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=6))

    @validates("email")
    def validate_email_field(self, value: str):
        if not validate_email(value):
            raise ValidationError("Invalid email format")


class CartAddSchema(BaseSchema):
    product_id = fields.Integer(required=True, validate=validate.Range(min=1))
    quantity = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1),
    )


class CartUpdateSchema(BaseSchema):
    product_id = fields.Integer(required=True, validate=validate.Range(min=1))
    quantity = fields.Integer(required=True, validate=validate.Range(min=0))


class CartRemoveSchema(BaseSchema):
    product_id = fields.Integer(required=True, validate=validate.Range(min=1))

