require File.expand_path('../lib/opener/constituent_parsers/nl/version', __FILE__)

Gem::Specification.new do |gem|
  gem.name        = 'opener-constituent-parser-nl'
  gem.version     = Opener::ConstituentParsers::NL::VERSION
  gem.authors     = ['development@olery.com']
  gem.summary     = 'Constituent Parser for dutch using Alpino.'
  gem.description = gem.summary
  gem.homepage    = 'http://opener-project.github.com/'
  gem.extensions  = ['ext/hack/Rakefile']

  gem.required_ruby_version = '>= 1.9.2'

  gem.files = Dir.glob([
    'core/*',
    'ext/**/*',
    'lib/**/*',
    '*.gemspec',
    '*_requirements.txt',
    'README.md',
    'task/*'
  ]).select { |file| File.file?(file) }

  gem.executables = Dir.glob('bin/*').map { |file| File.basename(file) }

  gem.add_dependency 'rake'
  gem.add_dependency 'nokogiri'
  gem.add_dependency 'cliver'

  gem.add_development_dependency 'rspec', '~> 3.0'
  gem.add_development_dependency 'cucumber'
end
