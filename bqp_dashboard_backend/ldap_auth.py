import ldap

import logging

def ldap_authentication(identity, password):
    """
    This function attempts to authenticate a user via LDAP.

    Parameters:
    identity (str): The identity to authenticate
    password (str): The password to authenticate

    Returns:
    User Object: if authentication is successful, None otherwise
    """

    ldap_server = "ldaps://auth.sim.lrz.de:636"
    base_dn = "ou=Intranet,ou=Kennungen,o=lrz-muenchen,c=de"
    user_dn = f"cn={identity},ou=Intranet,ou=Kennungen,o=lrz-muenchen,c=de"
    search_filter = f"(&(cn={identity})(mwnLRZAbteilung=QCT))"
    attr_list = ['cn', 'mwnAuthUserKontaktEmail', 'mwnSn', ]
    try:
        # connect to ldap-server
        connect = ldap.initialize(ldap_server)
        connect.protocol_version = ldap.VERSION3
        # required for AD authentication
        connect.set_option(ldap.OPT_REFERRALS, 0)
        auth_user = connect.simple_bind_s(user_dn, password)
        # logging.warning(auth_user)
        if auth_user is None:
            print("Identity is not found!")
            return None

        ldap_user = connect.search_s(
            base_dn,
            ldap.SCOPE_SUBTREE,
            search_filter,
            attr_list
        )
        # return True
        return ldap_user

    except ldap.INVALID_CREDENTIALS:
        # If the credentials are invalid, return False
        return None
    except Exception as e:
        # Log any other exceptions that may occur
        print(f"Error: {e}")
        return None
    finally:
        # close the connection to the server
        connect.unbind_s()







