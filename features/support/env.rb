require_relative '../../lib/opener/constituent_parsers/nl'
require 'rspec'
require 'tempfile'

def kernel_root
  File.expand_path("../../../", __FILE__)
end

def kernel
  return Opener::ConstituentParsers::NL.new(
    :args => ['--no-time']
  )
end

RSpec.configure do |config|
  config.expect_with :rspec do |c|
    c.syntax = [:should, :expect]
  end

  config.mock_with :rspec do |c|
    c.syntax = [:should, :expect]
  end
end
