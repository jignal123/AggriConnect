from django.db import models
from Admin.models import AbstractClassForAll
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from datetime import date


class CropMaster(AbstractClassForAll):
    crop_id = models.AutoField(primary_key=True)
    crop_name = models.CharField(max_length=50)
    crop_variety = models.CharField(max_length=100)
    photo = models.ImageField(upload_to="crops/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)


class Farmer(AbstractClassForAll):

    class Gender(models.TextChoices):
        MALE = "M", _("MALE")
        FEMALE = "F", _("FEMALE")

    username_validator = UnicodeUsernameValidator()
    f_id = models.AutoField(primary_key=True)
    user_name = models.CharField(
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    password = models.CharField(max_length=128)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, default="")
    gender = models.CharField(max_length=1, choices=Gender.choices)
    sub_district = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    address = models.CharField(max_length=255, default="")
    ekyf_id = models.CharField(max_length=15, unique=True)
    f_phone = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                regex=r"^[0-9]{10,11}$",
                message="Enter a valid 10 or 11 digit Phone number.",
            )
        ],
    )
    f_photo = models.ImageField(upload_to="farmer/", blank=True, null=True)
    aadhar_no = models.CharField(
        max_length=12,
       validators=[
            RegexValidator(
                regex=r"^[2-9]{1}[0-9]{11}$",
                message="Invalid Adhaar card Number. Please Enter Valid Adhaar card Number"
            )
        ],
        unique=True,
        error_messages={"unique": _("Adhaar No Alredy Exist in the site")},
    )
    stock = models.ManyToManyField(CropMaster, through="StockMaster")


class StockMaster(AbstractClassForAll):
    stock_id = models.AutoField(primary_key=True)
    crop_id = models.ForeignKey(CropMaster, on_delete=models.CASCADE,related_name="fcrops")
    farmer_id = models.ForeignKey(Farmer, on_delete=models.CASCADE)


class StockDetail(AbstractClassForAll):
    class Units(models.TextChoices):
        KG = "kg", _("Kilograms")
        GRAM = "g", _("Grams")
        TON = "TON", _("Metric Tons")
        QUINTAL = "Q", _("Quintal (100kg)")

    stock_id = models.ForeignKey(StockMaster, on_delete=models.CASCADE,related_name="items")
    harvested_date = models.DateField(default=date.today)
    hectares = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True
    )
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=3, choices=Units.choices)
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)
    expiry_date = models.DateField(null=True)
    stored_location = models.CharField(max_length=255, blank=True, null=True)

    @property
    def total_price(self):
        return self.quantity * self.price_per_unit


class Listing(AbstractClassForAll):
    class Status(models.TextChoices):
        OPEN = "O", _("Open")
        RESERVED = "R", _("Reserved")
        SOLD = "S", _("SOLD")

    l_id = models.AutoField(primary_key=True)
    stock_detail = models.ForeignKey(StockDetail, on_delete=models.CASCADE)
    qty_available = models.DecimalField(max_digits=8, decimal_places=2)
    price_per_unit = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=1, choices=Status.choices,default=Status.OPEN)
