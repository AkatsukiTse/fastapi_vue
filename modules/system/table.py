from datetime import datetime

from sqlalchemy import String, Integer, DateTime, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from core.db import Base, CoreBaseMixin, TimeBaseMixin, OperatorBaseMixin, RemarkBaseMixin


class SysUser(Base, CoreBaseMixin, RemarkBaseMixin):
    __tablename__ = 'sys_user'

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dept_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    user_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    nick_name: Mapped[str] = mapped_column(String(64), nullable=True)
    user_type: Mapped[str] = mapped_column(String(2), nullable=True, default='00', comment='用户类型')
    email: Mapped[str] = mapped_column(String(128), nullable=True)
    phonenumber: Mapped[str] = mapped_column(String(11), nullable=True)
    sex: Mapped[str] = mapped_column(String(1), nullable=True, default='2', comment='0=男,1=女,2=未知')
    avatar: Mapped[str] = mapped_column(String(128), nullable=True)
    password: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='帐号状态（0正常 1停用）')
    login_ip: Mapped[str] = mapped_column(String(50), nullable=True, comment='最后登陆IP')
    login_date: Mapped[datetime] = mapped_column(DateTime, nullable=True, comment='最后登陆时间')


class SysRole(Base, CoreBaseMixin, RemarkBaseMixin):
    __tablename__ = 'sys_role'
    role_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(64), nullable=False)
    role_key: Mapped[str] = mapped_column(String(64), nullable=True, comment='角色权限')
    role_sort: Mapped[int] = mapped_column(Integer, nullable=True, comment='角色排序')
    data_scope: Mapped[str] = mapped_column(String(64), nullable=True,
                                            comment='（1：所有数据权限；2：自定义数据权限；3：本部门数据权限；4：本部门及以下数据权限；5：仅本人数据权限）')
    menu_check_strictly: Mapped[bool] = mapped_column(Integer, nullable=True, comment='菜单树选择项是否关联显示')
    dept_check_strictly: Mapped[bool] = mapped_column(Integer, nullable=True, comment='部门树选择项是否关联显示')
    status: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='角色状态（0正常 1停用）')


class SysUserRole(Base):
    __tablename__ = 'sys_user_role'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    role_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)


class SysDept(Base, CoreBaseMixin):
    __tablename__ = 'sys_dept'
    dept_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ancestors: Mapped[str] = mapped_column(String(50), nullable=False)
    dept_name: Mapped[str] = mapped_column(String(30), nullable=False)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leader: Mapped[str] = mapped_column(String(20), nullable=True)
    phone: Mapped[str] = mapped_column(String(11), nullable=True)
    email: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='部门状态（0正常 1停用）')


class SysRoleDept(Base):
    __tablename__ = 'sys_role_dept'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    dept_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)


class SysPost(Base, TimeBaseMixin, OperatorBaseMixin, RemarkBaseMixin):
    __tablename__ = 'sys_post'
    post_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_code: Mapped[str] = mapped_column(String(64), nullable=False)
    post_name: Mapped[str] = mapped_column(String(50), nullable=False)
    post_sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='岗位状态（0正常 1停用）')


class SysUserPost(Base):
    __tablename__ = 'sys_user_post'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    post_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)


class SysNotice(Base, OperatorBaseMixin, TimeBaseMixin, RemarkBaseMixin):
    __tablename__ = 'sys_notice'
    notice_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    notice_title: Mapped[str] = mapped_column(String(50), nullable=False)
    notice_type: Mapped[str] = mapped_column(String(1), nullable=False, default='1', comment='公告类型（1通知 2公告）')
    notice_content: Mapped[str] = mapped_column(String(2000), nullable=False)
    status: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='公告状态（0正常 1停用）')


class SysMenu(Base, OperatorBaseMixin, TimeBaseMixin, RemarkBaseMixin):
    __tablename__ = 'sys_menu'
    menu_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    menu_name: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    order_num: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    path: Mapped[str] = mapped_column(String(200), nullable=True)
    component: Mapped[str] = mapped_column(String(255), nullable=True)
    is_frame: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='是否为外链（0是 1否）')
    is_cache: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='是否缓存（0缓存 1不缓存）')
    menu_type: Mapped[str] = mapped_column(String(1), nullable=False, default='C',
                                           comment='菜单类型（M目录 C菜单 F按钮）')
    query: Mapped[str] = mapped_column(String(255), nullable=True)
    visible: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='菜单状态（0显示 1隐藏）')
    status: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='菜单状态（0正常 1停用）')
    perms: Mapped[str] = mapped_column(String(100), nullable=True, comment='权限标识')
    icon: Mapped[str] = mapped_column(String(100), nullable=True, comment='图标')


class SysRoleMenu(Base):
    __tablename__ = 'sys_role_menu'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    menu_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)


class SysConfig(Base):
    __tablename__ = 'sys_config'
    config_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    config_name: Mapped[str] = mapped_column(String(100), nullable=False)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False)
    config_value: Mapped[str] = mapped_column(String(500), nullable=False)
    config_type: Mapped[str] = mapped_column(String(1), nullable=False, default='Y',
                                             comment='系统内置（Y是 N否）')
    remark: Mapped[str] = mapped_column(VARCHAR(500), default='')

    create_time: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False, index=True)
    update_time: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, nullable=True)
    create_by: Mapped[str] = mapped_column(VARCHAR(64), nullable=False, index=True)
    update_by: Mapped[str] = mapped_column(VARCHAR(64), nullable=True)


class SysDictType(Base, OperatorBaseMixin, TimeBaseMixin, RemarkBaseMixin):
    __tablename__ = 'sys_dict_type'
    dict_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dict_name: Mapped[str] = mapped_column(String(100), nullable=False)
    dict_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='状态（0正常 1停用）')


class SysDictData(Base):
    __tablename__ = 'sys_dict_data'
    dict_code: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    dict_sort: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dict_label: Mapped[str] = mapped_column(String(100), nullable=False)
    dict_value: Mapped[str] = mapped_column(String(100), nullable=False)
    dict_type: Mapped[str] = mapped_column(String(100), nullable=False)
    css_class: Mapped[str] = mapped_column(String(100), nullable=True)
    list_class: Mapped[str] = mapped_column(String(100), nullable=True)
    is_default: Mapped[str] = mapped_column(String(1), nullable=False, default='N', comment='是否默认（Y是 N否）')
    status: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='状态（0正常 1停用）')
    remark: Mapped[str] = mapped_column(String(500), nullable=True)

    create_time: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False, index=True)
    update_time: Mapped[datetime] = mapped_column(default=datetime.now, onupdate=datetime.now, nullable=True)
    create_by: Mapped[str] = mapped_column(VARCHAR(64), nullable=False, index=True)
    update_by: Mapped[str] = mapped_column(VARCHAR(64), nullable=True)


class SysOperLog(Base):
    __tablename__ = 'sys_oper_log'
    oper_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False, comment='模块标题')
    business_type: Mapped[str] = mapped_column(String(1), nullable=False, comment='业务类型（0=其它,1=新增,2=修改,3=删除,4=授权,5=导出,6=导入,7=强退,8=生成代码,9=清空数据）')
    method: Mapped[str] = mapped_column(String(100), nullable=False, comment='方法名称')
    request_method: Mapped[str] = mapped_column(String(10), nullable=False, comment='请求方式')
    operator_type: Mapped[str] = mapped_column(String(1), nullable=False, comment='操作类别（0其它 1后台用户 2手机端用户）')
    oper_name: Mapped[str] = mapped_column(String(50), nullable=False, comment='操作人员')
    dept_name: Mapped[str] = mapped_column(String(50), nullable=False, comment='部门名称')
    oper_url: Mapped[str] = mapped_column(String(255), nullable=False, comment='请求URL')
    oper_ip: Mapped[str] = mapped_column(String(50), nullable=False, comment='主机地址')
    oper_location: Mapped[str] = mapped_column(String(255), nullable=True, comment='操作地点')
    oper_param: Mapped[str] = mapped_column(String(2000), nullable=True, comment='请求参数')
    json_result: Mapped[str] = mapped_column(String(2000), nullable=True, comment='返回参数')
    status: Mapped[str] = mapped_column(String(1), nullable=False, default='0', comment='操作状态（0正常 1异常）')
    error_msg: Mapped[str] = mapped_column(String(2000), nullable=True, comment='错误消息')
    oper_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, comment='操作时间')
    cost_time: Mapped[int] = mapped_column(Integer, nullable=False, comment='耗时')
