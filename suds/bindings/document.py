# This program is free software; you can redistribute it and/or modify
# it under the terms of the (LGPL) GNU Lesser General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library Lesser General Public License for more details at
# ( http://www.gnu.org/licenses/lgpl.html ).
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# written by: Jeff Ortel ( jortel@redhat.com )

"""
Provides classes for the (WS) SOAP I{document/literal}.
"""

from suds import *
from suds.bindings.binding import Binding
from suds.sax.element import Element


class Document(Binding):
    """
    The document/literal style. Literal is the only (@use) supported since
    document/encoded is pretty much dead.

    Although the SOAP specification supports multiple documents within the SOAP
    <body/>, it is very uncommon. As such, suds library supports presenting an
    I{RPC} view of service methods defined with only a single document
    parameter. To support the complete specification, service methods defined
    with multiple documents (multiple message parts), are still presented using
    a full I{document} view.

    More detailed description:

    An interface is considered I{wrapped} if:
      - There is exactly one message part in that interface.
      - The message part resolves to an element of a non-builtin type.
    Otherwise it is considered I{bare}.

    I{Bare} interface is Interpreted directly as specified in the WSDL schema,
    with each message part represented by a single parameter in the suds
    library web service operation proxy interface (input or output).

    I{Wrapped} interface is interpreted without the external wrapping document
    structure, with each of its contained elements passed through suds
    library's web service operation proxy interface (input or output)
    individually instead of as a single I{document} object.

    """
    def bodycontent(self, method, args, kwargs):
        if not len(method.soap.input.body.parts):
            return ()
        wrapped = method.soap.input.body.wrapped
        if wrapped:
            pts = self.bodypart_types(method)
            root = self.document(pts[0])
        else:
            root = []
        args = list(args)
        params = self.param_defs(method)
        params_count = len(args) + len(kwargs)
        params_specified = set()
        params_have_choice = False
        params_choice_value_defined = False
        params_choice_optional = False
        params_required = 0
        params_possible = 0
        for pd in params:
            is_choice_param = len(pd) > 2 and pd[2]
            is_optional_param = pd[1].optional()

            params_possible += 1
            if is_choice_param:
                params_have_choice = True
                # A choice is considered optional if any of its elements are
                # optional. This means that we do not know whether to count the
                # whole choice structure as a single required parameter or not
                # until after we are done processing all of its contained
                # elements.
                #
                # We should also check whether the whole choice element has
                # been explicitly marked as optional, but this is not currently
                # supported in suds for neither all, choice nor sequence order
                # indicators.
                if is_optional_param:
                    params_choice_optional = True
            else:
                if not is_optional_param:
                    params_required += 1

            value_specified = True
            value = None
            if args:
                value = args.pop(0)
            else:
                try:
                    value = kwargs.pop(pd[0])
                except KeyError:
                    value_specified = False

            if value_specified:
                # Note that since params_specified is a set, it tracks all
                # same-named input parameters as one. This is not a problem, in
                # and of itself, as the rest of suds also does not support this
                # use case.
                params_specified.add(pd[0])

            if is_choice_param:
                if value is not None:
                    if params_choice_value_defined:
                        msg = ("%s() got multiple arguments belonging to a "
                            "single choice parameter group.")
                        raise TypeError(msg % (method.name,))
                    params_choice_value_defined = True
                # Skip non-existing by-choice arguments.
                # Implementation notes:
                #   * This functionality might be better placed inside the
                #     mkparam() function but to do that we would first need to
                #     understand more thoroughly how different Binding
                #     subclasses in suds work and how they would be affected by
                #     this change.
                #   * An empty choice parameter can be specified by explicitly
                #     providing an empty string value for it.
                if value is None:
                    continue
            p = self.mkparam(method, pd, value)
            if p is None:
                continue
            if not wrapped:
                ns = pd[1].namespace('ns0')
                p.setPrefix(ns[0], ns[1])
            root.append(p)
        if kwargs:
            arg_name = kwargs.keys()[0]
            if arg_name in params_specified:
                msg = "%s() got multiple values for argument '%s'"
            else:
                msg = "%s() got an unexpected keyword argument '%s'"
            raise TypeError(msg % (method.name, arg_name))
        if args:
            if params_have_choice and not params_choice_optional:
                params_required += 1
            def plural_suffix(count):
                if count == 1:
                    return ""
                return "s"
            def plural_was_were(count):
                if count == 1:
                    return "was"
                return "were"
            expected = params_required
            if params_required != params_possible:
                expected = "%d to %d" % (params_required, params_possible)
            given = params_count
            msg_parts = ["%s() takes %s argument" % (method.name, expected),
                plural_suffix(expected), " but %d " % (given,),
                plural_was_were(given), " given"]
            raise TypeError("".join(msg_parts))
        return root

    def replycontent(self, method, body):
        wrapped = method.soap.output.body.wrapped
        if wrapped:
            return body[0].children
        return body.children

    def document(self, wrapper):
        """
        Get the document root. For I{document/literal}, this is the name of the
        wrapper element qualifed by the schema's target namespace.
        @param wrapper: The method name.
        @type wrapper: L{xsd.sxbase.SchemaObject}
        @return: A root element.
        @rtype: L{Element}
        """
        tag = wrapper[1].name
        ns = wrapper[1].namespace('ns0')
        d = Element(tag, ns=ns)
        return d

    def mkparam(self, method, pdef, object):
        """
        Expand list parameters into individual parameters each with the type
        information. This is because in document arrays are simply
        multi-occurrence elements.

        """
        if isinstance(object, (list, tuple)):
            tags = []
            for item in object:
                tags.append(self.mkparam(method, pdef, item))
            return tags
        return Binding.mkparam(self, method, pdef, object)

    def param_defs(self, method):
        """Get parameter definitions for document literal."""
        pts = self.bodypart_types(method)
        wrapped = method.soap.input.body.wrapped
        if not wrapped:
            return pts
        result = []
        # wrapped
        for p in pts:
            resolved = p[1].resolve()
            for child, ancestry in resolved:
                if child.isattr():
                    continue
                result.append((child.name, child, self.bychoice(ancestry)))
        return result

    def returned_types(self, method):
        result = []
        wrapped = method.soap.output.body.wrapped
        rts = self.bodypart_types(method, input=False)
        if wrapped:
            for pt in rts:
                resolved = pt.resolve(nobuiltin=True)
                for child, ancestry in resolved:
                    result.append(child)
                break
        else:
            result += rts
        return result

    def bychoice(self, ancestry):
        """
        The ancestry contains a <choice/>
        @param ancestry: A list of ancestors.
        @type ancestry: list
        @return: True if contains <choice/>
        @rtype: boolean
        """
        for x in ancestry:
            if x.choice():
                return True
        return False
