from typing import TypeVar, Generic, Any, List, Optional, Annotated
from fastapi import Query, Depends
from pydantic import BaseModel, ConfigDict, create_model, BeforeValidator
from pydantic.alias_generators import to_camel

T = TypeVar('T')


class ResponseCode(object):
    """响应码"""
    SUCCESS = 200
    BAD_REQUEST = 400
    CAPTCHA_TIMEOUT = 400
    CAPTCHA_ERROR = 400
    LOGIN_EXPIRE = 400
    LOGIN_REQUIRE = 400
    PERMISSION_DENY = 400
    SYSTEM_ERROR = 500


class _PageParams:
    """分页查询参数"""

    def __init__(self, page_num: int = Query(1, alias='pageNum'),
                 page_size: int = Query(10, alias='pageSize')):
        self.page_num = page_num
        self.page_size = page_size


PageParams = Annotated[_PageParams, Depends()]

camel_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CamelModel(BaseModel):
    model_config = camel_config


class BaseResponse(CamelModel):
    """基础返回结构"""
    code: int = ResponseCode.SUCCESS
    msg: str = ''
    data: Optional[Any] = None

    @classmethod
    def ok(cls, data=None):
        return cls(data=data)


class TableDataInfo(BaseModel, Generic[T]):
    total: int
    rows: List[T]
    code: int = ResponseCode.SUCCESS
    msg: str = ''


class TreeSelect(CamelModel):
    id: int
    parent_id: int
    label: str
    children: Optional[List['TreeSelect']] = []

    @classmethod
    def build_tree(cls,
                   data_list: List,
                   id_key='id',
                   label_key='label',
                   parent_key='parent_id',
                   root_parent_value=0) -> List['TreeSelect']:
        tree_data_list = [cls(
            id=getattr(data, id_key),
            label=getattr(data, label_key),
            parent_id=getattr(data, parent_key),
            children=[]) for data in data_list]
        for tree_data in tree_data_list:
            tree_data.children = [child for child in tree_data_list if child.parent_id == tree_data.id]
        return [tree_data for tree_data in tree_data_list if tree_data.parent_id == root_parent_value]


_exclude_fields = ['create_by', 'create_time', 'update_by', 'update_time', 'del_flag']


def make_optional_dto(entity, exclude_fields=None) -> type[BaseModel]:
    """
    根据Table对象快捷生成Optional DTO
    """
    if exclude_fields is None:
        exclude_fields = _exclude_fields
    fields = {col.name: (Optional[col.type.python_type], None) for col in entity.__table__.columns if
              col.name not in exclude_fields}
    return create_model(f'Optional{entity.__name__}DTO', **fields, __config__=camel_config)


def make_query_dto(*attributes) -> type[BaseModel]:
    """
    创建查询DTO的快捷函数
    :param attributes: 查询字段
    """
    fields = {attr: (Optional[Any], Query(default=None)) for attr in attributes}

    # Create a dynamic Pydantic model
    dto_class = create_model('DynamicQueryDTO', **fields)

    return dto_class


def convert_int_to_str(v):
    if isinstance(v, int):
        return str(v)
    return v


def convert_str_to_int(v):
    if isinstance(v, str):
        if v.isalnum():
            return int(v)
    return v


AutoString = Annotated[str, BeforeValidator(convert_int_to_str)]
AutoInt = Annotated[int, BeforeValidator(convert_str_to_int)]
