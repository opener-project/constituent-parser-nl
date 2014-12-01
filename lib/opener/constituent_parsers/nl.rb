require 'nokogiri'
require 'open3'

require_relative 'nl/version'

module Opener
  module ConstituentParsers

    ##
    # The constituent parser that supports Dutch.
    #
    # @!attribute [r] args
    #  @return [Array]
    #
    # @!attribute [r] options
    #  @return [Hash]
    #
    class NL
      attr_reader :args, :options

      ##
      # @param [Hash] options
      #
      # @option options [Array] :args Extra commandline arguments to use.
      #
      def initialize(options = {})
        @args    = options.delete(:args) || []
        @options = options
      end

      ##
      # Builds the command used to execute the kernel.
      #
      # @param [Array] args Commandline arguments passed to the command.
      #
      def command
        return "#{adjust_python_path} python #{kernel} #{args.join(' ')}"
      end

      ##
      # Runs the command and returns the output of STDOUT, STDERR and the
      # process information.
      #
      # @param [String] input The input to tag.
      # @return [String]
      #
      def run(input)
        stdout, stderr, process = capture(input)

        raise stderr unless process.success?

        return stdout.strip
      end

      protected

      ##
      # @return [String]
      #
      def adjust_python_path
        site_packages =  File.join(core_dir, 'site-packages/pre_install')

        return "env PYTHONPATH=#{site_packages}:$PYTHONPATH"
      end

      ##
      # capture3 method doesn't work properly with Jruby, so
      # this is a workaround
      #
      def capture(input)
        Open3.popen3(*command.split(" ")) {|i, o, e, t|
          out_reader = Thread.new { o.read }
          err_reader = Thread.new { e.read }
          i.write input
          i.close
          [out_reader.value, err_reader.value, t.value]
        }
      end

      ##
      # @return [String]
      #
      def core_dir
        return File.expand_path('../../../../core', __FILE__)
      end

      ##
      # @return [String]
      #
      def kernel
        return File.join(core_dir, 'alpino_parser.py')
      end
    end # NL
  end # ConstituentParsers
end # Opener
