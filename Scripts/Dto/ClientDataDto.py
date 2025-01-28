from typing import List
from enum import Enum
import json

class Permission(Enum):
    SPOT = 0

    @staticmethod
    def from_str(permission: str):
        try:
            return Permission[permission]
        except KeyError:
            raise ValueError(f"Unknown permission: {permission}")

    def to_dict(self):
        return {'permission': self.name}

class BalanceAsset:
    def __init__(self, asset: str, free: float, locked: float):
        self.asset = asset
        self.free = free
        self.locked = locked

    @staticmethod
    def from_dict(data: dict):
        return BalanceAsset(
            asset=data['asset'],
            free=float(data['free']),
            locked=float(data['locked'])
        )

    def to_dict(self):
        return {
            'asset': self.asset,
            'free': self.free,
            'locked': self.locked
        }

class ComissionRate:
    def __init__(self, maker: float = 0.001, taker: float = 0.001, buyer: float = 0.0, seller: float = 0.0):
        self.maker = maker
        self.taker = taker
        self.buyer = buyer
        self.seller = seller

    @staticmethod
    def from_dict(data: dict):
        return ComissionRate(
            maker=float(data['maker']),
            taker=float(data['taker']),
            buyer=float(data['buyer']),
            seller=float(data['seller'])
        )

    def to_dict(self):
        return {
            'maker': self.maker,
            'taker': self.taker,
            'buyer': self.buyer,
            'seller': self.seller
        }

class ClientDataDto:
    def __init__(self, makerCommission: float = 0.0, takerCommission: float = 0.0, buyerCommission: float = 0.0,
                 sellerCommission: float = 0.0, commissionRates: ComissionRate = ComissionRate(), canTrade: bool = True,
                 canWithdraw: bool = True, canDeposit: bool = True, brokered: bool = False,
                 requireSelfTradePrevention: bool = False, preventSor: bool = False, updateTime: float = 1723429854440,
                 accountType: str = 'SPOT', balances: List[BalanceAsset] = None, permissions: List[Permission] = None,
                 uid: str = ''):
        self.makerCommission = makerCommission
        self.takerCommission = takerCommission
        self.buyerCommission = buyerCommission
        self.sellerCommission = sellerCommission
        self.commissionRates = commissionRates
        self.canTrade = canTrade
        self.canWithdraw = canWithdraw
        self.canDeposit = canDeposit
        self.brokered = brokered
        self.requireSelfTradePrevention = requireSelfTradePrevention
        self.preventSor = preventSor
        self.updateTime = updateTime
        self.accountType = accountType
        self.balances = balances if balances is not None else []
        self.permissions = permissions if permissions is not None else []
        self.uid = uid

    @staticmethod
    def from_dict(data: dict):
        return ClientDataDto(
            makerCommission=data['makerCommission'],
            takerCommission=data['takerCommission'],
            buyerCommission=data['buyerCommission'],
            sellerCommission=data['sellerCommission'],
            commissionRates=ComissionRate.from_dict(data['commissionRates']),
            canTrade=data['canTrade'],
            canWithdraw=data['canWithdraw'],
            canDeposit=data['canDeposit'],
            brokered=data['brokered'],
            requireSelfTradePrevention=data['requireSelfTradePrevention'],
            preventSor=data['preventSor'],
            updateTime=data['updateTime'],
            accountType=data['accountType'],
            balances=[BalanceAsset.from_dict(balance) for balance in data['balances']],
            permissions=[Permission.from_str(permission) for permission in data['permissions']],
            uid=data['uid']
        )

    def to_dict(self):
        return {
            'makerCommission': self.makerCommission,
            'takerCommission': self.takerCommission,
            'buyerCommission': self.buyerCommission,
            'sellerCommission': self.sellerCommission,
            'commissionRates': self.commissionRates.to_dict(),
            'canTrade': self.canTrade,
            'canWithdraw': self.canWithdraw,
            'canDeposit': self.canDeposit,
            'brokered': self.brokered,
            'requireSelfTradePrevention': self.requireSelfTradePrevention,
            'preventSor': self.preventSor,
            'updateTime': self.updateTime,
            'accountType': self.accountType,
            'balances': [balance.to_dict() for balance in self.balances],
            'permissions': [permission.name for permission in self.permissions],  # .name for enums
            'uid': self.uid
        }

    def __str__(self):
        return json.dumps(self.to_dict(), indent=4)