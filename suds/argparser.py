# -*- coding: utf-8 -*-

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
# written by: Jurko Gospodnetić jurko.gospodnetic@pke.hr )

"""
Suds web service operation invocation function argument parser.

See the ArgParser class description for more detailed information.

"""

__all__ = ["ArgParser"]


class ArgParser:
    """
    Argument parser for suds web service operation invocation functions.

    Suds prepares Python function objects for invoking web service operations.
    This parser implements generic binding agnostic part of processing the
    arguments passed when calling those function objects.

    Expects to be passed the web service operation's parameter definitions in
    order (process_parameter() method) and, based on that, extracts the values
    for those parameter from the arguments provided in the web service
    operation invocation call.

    After all the web service operation's parameters have been processed, the
    argument processing is completed by calling the argument parser's finish()
    method.

    During processing, each parameter's definition and value, together with any
    additional pertinent information collected from the encountered parameter
    definition structure, is passed on to the provided external parameter
    processor function. There that information is expected to be used to
    construct the actual binding specific web service operation invocation
    request. Note that, depending on the input parameter structure, needed
    parameter information may not be available until some later time (e.g.
    after some later parameter processing has been completed) and so forwarding
    that information to the external parameter processor function may not occur
    directly during that parameter's processing, but will occur in the final
    finish() method call at the latest.

    Performs generic, binding agnostic, argument checking and raises a
    TypeError exception in case any errors are detected. The exceptions raised
    have been constructed to make them as similar as possible to their
    respective exceptions raised during regular Python function argument
    checking.

    Does not support multiple same-named input parameters.

    """

    def __init__(self, method_name, wrapped, args, kwargs,
            external_param_processor):
        """
        Constructs a new ArgParser instance.

        Passed args & kwargs objects are considered owned by the new argument
        parser instance and may be modified internally during parsing.

        """
        self.__method_name = method_name
        self.__wrapped = wrapped
        self.__external_param_processor = external_param_processor
        self.__args = list(args)
        self.__kwargs = kwargs
        self.__args_count = len(args) + len(kwargs)
        self.__params_with_arguments = set()
        self.__stack = []
        self.__push_frame(None)

    def active(self):
        """Return whether argument processing is still unfinished."""
        return bool(self.__stack)

    def finish(self):
        """
        Finish the argument processing.

        May only be called after all the web service operation's parameters
        have been successfully processed and, afterwards, no further parameter
        processing is allowed.

        See the ArgParser class description for more detailed information.

        """
        if not self.active():
            raise RuntimeError("finish() called on an inactive ArgParser.")
        bottom = self.__stack[0]
        self.__pop_frames_above(bottom)
        self.__check_for_extra_arguments()
        self.__pop_top_frame()
        assert not self.__stack

    def process_parameter(self, param_name, param_type, ancestry=None):
        """
        Collect arguments for the given web service operation input parameter.

        Definitions for regular web service parameters, i.e. those defined
        directly as message parts in the web service operation's WSDL schema,
        are expected to include no additional 'ancestry' information.

        Parameter definitions for parameters constructed based on suds
        library's automatic input parameter structure unwrapping, are expected
        to include the parameter's XSD schema 'ancestry' context, i.e. a list
        of all the parent XSD schema tags containing the parameter's <element>
        tag. Such ancestry context provides detailed information about how the
        parameter's value is expected to be used.

        Rules on acceptable ancestry items:
          * Ancestry item's choice() method must return whether the item
            represents a <choice> XSD schema tag.
          * Passed ancestry items are used 'by address' internally and the same
            XSD schema tag is expected to be identified by the exact same
            ancestry item object during the whole argument processing.

        See the ArgParser class description for more detailed information.

        """
        if not self.active():
            raise RuntimeError("process_parameter() called on an inactive "
                "ArgParser.")
        if self.__wrapped and not ancestry:
            raise RuntimeError("Automatically unwrapped interfaces require "
                "ancestry information specified for all their parameters.")
        if not self.__wrapped and (ancestry is not None):
            raise RuntimeError("Only automatically unwrapped interfaces may "
                "have their parameter ancestry information specified.")
        param_optional = param_type.optional()
        has_argument, value = self.__get_param_value(param_name)
        if has_argument:
            self.__params_with_arguments.add(param_name)
        self.__update_context(ancestry)
        self.__stack[-1].process_parameter(param_optional, value is not None)
        self.__external_param_processor(param_name, param_type,
            self.__in_choice_context(), value)

    def __check_for_extra_arguments(self):
        """
        Report an error in case any extra arguments are detected.

        May only be called after the argument processing has completed, all the
        regular context frames have been popped off the stack and the only
        remaining frame there is the sentinel holding the final processing
        results.

        """
        assert len(self.__stack) == 1
        sentinel_frame = self.__stack[0]
        args_required = sentinel_frame.args_required()
        args_allowed = sentinel_frame.args_allowed()

        if self.__kwargs:
            param_name = self.__kwargs.keys()[0]
            if param_name in self.__params_with_arguments:
                msg = "got multiple values for parameter '%s'"
            else:
                msg = "got an unexpected keyword argument '%s'"
            self.__error(msg % (param_name,))

        if self.__args:
            def plural_suffix(count):
                if count == 1:
                    return ""
                return "s"
            def plural_was_were(count):
                if count == 1:
                    return "was"
                return "were"
            expected = args_required
            if args_required != args_allowed:
                expected = "%d to %d" % (args_required, args_allowed)
            given = self.__args_count
            msg_parts = ["takes %s positional argument" % (expected,),
                plural_suffix(expected), " but %d " % (given,),
                plural_was_were(given), " given"]
            self.__error("".join(msg_parts))

    def __error(self, message):
        """Report an argument processing error."""
        raise TypeError("%s() %s" % (self.__method_name, message))

    def __frame_factory(self, ancestry_item):
        """Construct a new frame representing the given ancestry item."""
        frame_class = Frame
        if ancestry_item is not None and ancestry_item.choice():
            frame_class = ChoiceFrame
        return frame_class(ancestry_item, self.__error)

    def __get_param_value(self, name):
        """
        Extract a parameter value from the remaining given arguments.

        Returns a 2-tuple consisting of the following:
          * Boolean indicating whether an argument has been specified for the
            requested input parameter.
          * Parameter value.

        """
        if self.__args:
            return True, self.__args.pop(0)
        try:
            value = self.__kwargs.pop(name)
        except KeyError:
            return False, None
        return True, value

    def __in_choice_context(self):
        """
        Whether we are currently processing a choice parameter group.

        This includes processing a parameter defined directly or indirectly
        within such a group or not processing a parameter at the moment.

        May only be called during parameter processing or the result will be
        calculated based on the context left behind by the previous parameter
        processing if any.

        """
        for x in self.__stack:
            if x.__class__ is ChoiceFrame:
                return True
        return False

    def __match_ancestry(self, ancestry):
        """
        Find frames matching the given ancestry.

        If any frames have already been pushed to the current frame stack,
        except for the initial sentry frame, expects the given ancestry to
        match at least one of those frames. In other words, passed ancestries
        must all be related and lead back to the same root.

        Returns a tuple containing the following:
          * Topmost frame matching the given ancestry or the bottom-most sentry
            frame if no frame matches.
          * Unmatched ancestry part.

        """
        stack = self.__stack
        if len(stack) == 1:
            return stack[0], ancestry
        if stack[1].id() is not ancestry[0]:
            # This failing indicates that someone changed the logic detecting
            # whether a particular web service operation may have its
            # parameters automatically unwrapped. Currently it requires that
            # the operation have only a single input parameter to unwrap, thus, 
            # all unwrapped parameters come from that unwrapped parameter and
            # so share the same ancestry.
            raise RuntimeError("All automatically unwrapped parameter's need "
                "to share the same ancestry.")
        previous = stack[0]
        for frame, n in zip(stack[1:], xrange(len(ancestry))):
            if frame.id() is not ancestry[n]:
                return previous, ancestry[n:]
            previous = frame
        return frame, ancestry[n + 1:]

    def __pop_frames_above(self, frame):
        """Pops all the frames above, but not including the given frame."""
        while self.__stack[-1] is not frame:
            self.__pop_top_frame()
        assert self.__stack

    def __pop_top_frame(self):
        """Pops the top frame off the frame stack."""
        popped = self.__stack.pop()
        if self.__stack:
            self.__stack[-1].process_subframe(popped)

    def __push_frame(self, ancestry_item):
        """Push a new frame on top of the frame stack."""
        frame = self.__frame_factory(ancestry_item)
        self.__stack.append(frame)

    def __push_frames(self, ancestry):
        """Push new frames representing given ancestry items."""
        for x in ancestry:
            assert x is not None
            self.__push_frame(x)

    def __update_context(self, ancestry):
        assert self.__wrapped == bool(ancestry)
        if not ancestry:
            return
        match_result = self.__match_ancestry(ancestry)
        last_matching_frame, unmatched_ancestry = match_result
        self.__pop_frames_above(last_matching_frame)
        self.__push_frames(unmatched_ancestry)


class Frame:
    """
    Base ArgParser context frame.

    When used directly, as opposed to using a derived class, may represent any
    input parameter context/ancestry item except a choice order indicator.

    See the ArgParser class for more detailed information.

    """

    def __init__(self, id, error):
        """
        Construct a new Frame instance.

        Passed error function is used to report any argument checking errors.

        """
        assert self.__class__ != Frame or not id or not id.choice()
        self.__id = id
        self._error = error
        self._args_allowed = 0
        self._args_required = 0
        self._has_value = False

    def args_allowed(self):
        return self._args_allowed

    def args_required(self):
        return self._args_required

    def has_value(self):
        return self._has_value

    def id(self):
        return self.__id

    def process_parameter(self, optional, has_value):
        args_required = 1
        if optional:
            args_required = 0
        self._process_item(has_value, 1, args_required)

    def process_subframe(self, subframe):
        self._process_item(
            subframe.has_value(),
            subframe.args_allowed(),
            subframe.args_required())

    def _process_item(self, has_value, args_allowed, args_required):
        self._args_allowed += args_allowed
        self._args_required += args_required
        if has_value:
            self._has_value = True


class ChoiceFrame(Frame):
    """
    ArgParser context frame representing a choice order indicator.

    A choice requires as many input arguments as are needed to satisfy the
    least requiring of its items. For example, if we use I(n) to identify an
    item requiring n parameter, then a choice containing I(2), I(3) & I(7)
    requires 2 arguments while a choice containing I(5) & I(4) requires 4.

    Accepts an argument for each of its contained elements but allows at most
    one of its directly contained items to have a defined value.

    See the ArgParser class for more detailed information.

    """

    def __init__(self, id, error):
        assert id.choice()
        Frame.__init__(self, id, error)
        self.__has_item = False

    def _process_item(self, has_value, args_allowed, args_required):
        self._args_allowed += args_allowed
        self.__update_args_required_for_item(args_required)
        self.__update_has_value_for_item(has_value)

    def __update_args_required_for_item(self, item_args_required):
        if not self.__has_item:
            self.__has_item = True
            self._args_required = item_args_required
            return
        self._args_required = min(self.args_required(), item_args_required)

    def __update_has_value_for_item(self, item_has_value):
        if item_has_value:
            if self.has_value():
                self._error("got multiple values for a single choice "
                    "parameter")
            self._has_value = True
