#!/usr/bin/env python3
"""Tests for langman.py - Tree-sitter grammar builder and installer."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Import the module under test
import langman


# --- Fixtures ---
@pytest.fixture
def tmp_dirs(tmp_path):
    """Create temp cache/dist/install directories."""
    dirs = {
        'cache': tmp_path / '.cache',
        'dist': tmp_path / 'dist',
        'install': tmp_path / 'install',
    }
    for d in dirs.values():
        d.mkdir(parents=True)
    return dirs


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for git/cc/c++ calls."""
    with patch('langman.subprocess.run') as mock:
        mock.return_value = MagicMock(returncode=0, stdout='abc123\n')
        yield mock


# --- Platform Detection Tests ---
class TestPlatformDetection:
    @patch('platform.system', return_value='Darwin')
    def test_detect_extension_macos(self, _):
        assert langman.detect_extension() == 'dylib'

    @patch('platform.system', return_value='Linux')
    def test_detect_extension_linux(self, _):
        assert langman.detect_extension() == 'so'

    @patch('platform.system', return_value='Windows')
    def test_detect_extension_windows(self, _):
        assert langman.detect_extension() == 'dll'

    @patch('platform.system', return_value='Darwin')
    def test_detect_xattr_method_macos(self, _):
        assert langman.detect_xattr_method() == 'macos'

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which', side_effect=lambda x: x if x in ['setfattr', 'getfattr'] else None)
    def test_detect_xattr_method_linux(self, _, __):
        assert langman.detect_xattr_method() == 'linux'

    @patch('platform.system', return_value='Linux')
    @patch('shutil.which', return_value=None)
    def test_detect_xattr_method_fallback(self, _, __):
        assert langman.detect_xattr_method() == 'fallback'


# --- Language Config Tests ---
class TestLangConfig:
    def test_default_config(self):
        cfg = langman.get_lang_config('python')
        assert cfg.name == 'python'
        assert cfg.site == 'https://github.com'
        assert cfg.org == 'tree-sitter'
        assert cfg.repo is None  # uses default tree-sitter-python
        assert cfg.source_dir == 'src'
        assert cfg.branch is None

    def test_custom_org(self):
        cfg = langman.get_lang_config('ada')
        assert cfg.org == 'briot'

    def test_custom_site(self):
        cfg = langman.get_lang_config('bison')
        assert cfg.site == 'https://gitlab.com'
        assert cfg.org == 'btuin2'

    def test_custom_repo(self):
        cfg = langman.get_lang_config('gomod')
        assert cfg.org == 'camdencheek'
        assert cfg.repo == 'tree-sitter-go-mod'

    def test_custom_source_dir(self):
        cfg = langman.get_lang_config('markdown')
        assert cfg.source_dir == 'tree-sitter-markdown/src'

    def test_custom_branch(self):
        cfg = langman.get_lang_config('sql')
        assert cfg.org == 'DerekStride'
        assert cfg.branch == 'gh-pages'

    def test_tsx_config(self):
        cfg = langman.get_lang_config('tsx')
        assert cfg.org == 'tree-sitter'
        assert cfg.repo == 'tree-sitter-typescript'
        assert cfg.source_dir == 'tsx/src'

    def test_typescript_config(self):
        cfg = langman.get_lang_config('typescript')
        assert cfg.source_dir == 'typescript/src'

    def test_effective_repo_default(self):
        cfg = langman.get_lang_config('python')
        assert cfg.effective_repo == 'tree-sitter-python'

    def test_effective_repo_custom(self):
        cfg = langman.get_lang_config('gomod')
        assert cfg.effective_repo == 'tree-sitter-go-mod'

    def test_clone_url(self):
        cfg = langman.get_lang_config('python')
        assert cfg.clone_url == 'https://github.com/tree-sitter/tree-sitter-python.git'


class TestLoadLanguages:
    def test_load_languages_returns_list(self):
        languages = langman.load_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0

    def test_load_languages_contains_common(self):
        languages = langman.load_languages()
        assert 'python' in languages
        assert 'javascript' in languages
        assert 'rust' in languages


# --- Version Attribute Tests ---
class TestVersionAttrs:
    @patch('langman.detect_xattr_method', return_value='fallback')
    def test_fallback_set_get(self, _, tmp_path):
        p = tmp_path / 'test.dylib'
        p.touch()
        langman.set_version(p, 'v1.0')
        assert langman.get_version(p) == 'v1.0'
        assert langman.has_version(p) is True

    @patch('langman.detect_xattr_method', return_value='fallback')
    def test_get_version_not_set(self, _, tmp_path):
        p = tmp_path / 'test.dylib'
        p.touch()
        assert langman.get_version(p) is None
        assert langman.has_version(p) is False

    @patch('langman.detect_xattr_method', return_value='fallback')
    def test_fallback_version_file_location(self, _, tmp_path):
        p = tmp_path / 'test.dylib'
        p.touch()
        langman.set_version(p, 'v2.0')
        version_file = tmp_path / 'test.dylib.version'
        assert version_file.exists()
        assert version_file.read_text() == 'v2.0'

    @patch('langman.detect_xattr_method', return_value='macos')
    @patch('langman.subprocess.run')
    def test_macos_set_version(self, mock_run, _, tmp_path):
        mock_run.return_value = MagicMock(returncode=0)
        p = tmp_path / 'test.dylib'
        p.touch()
        langman.set_version(p, 'v1.0')
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'xattr'
        assert '-w' in call_args

    @patch('langman.detect_xattr_method', return_value='macos')
    @patch('langman.subprocess.run')
    def test_macos_get_version(self, mock_run, _, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stdout='v1.0\n')
        p = tmp_path / 'test.dylib'
        p.touch()
        result = langman.get_version(p)
        assert result == 'v1.0'

    @patch('langman.detect_xattr_method', return_value='linux')
    @patch('langman.subprocess.run')
    def test_linux_set_version(self, mock_run, _, tmp_path):
        mock_run.return_value = MagicMock(returncode=0)
        p = tmp_path / 'test.dylib'
        p.touch()
        langman.set_version(p, 'v1.0')
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'setfattr'


# --- Cache Tests ---
class TestCache:
    def test_cache_path(self, tmp_dirs):
        with patch.object(langman, 'CACHE_DIR', tmp_dirs['cache']):
            path = langman.cache_path('python', 'v1.0')
            assert path == tmp_dirs['cache'] / 'python' / 'v1.0'

    def test_is_cached_false_when_missing(self, tmp_dirs):
        with patch.object(langman, 'CACHE_DIR', tmp_dirs['cache']):
            with patch('langman.detect_extension', return_value='dylib'):
                assert langman.is_cached('python', 'v1.0') is False

    @patch('langman.detect_extension', return_value='dylib')
    @patch('langman.has_version', return_value=True)
    def test_is_cached_true_when_present(self, _, __, tmp_dirs):
        with patch.object(langman, 'CACHE_DIR', tmp_dirs['cache']):
            cache_dir = tmp_dirs['cache'] / 'python' / 'v1.0'
            cache_dir.mkdir(parents=True)
            artifact = cache_dir / 'libtree-sitter-python.dylib'
            artifact.touch()
            assert langman.is_cached('python', 'v1.0') is True

    @patch('langman.detect_extension', return_value='dylib')
    @patch('langman.has_version', return_value=True)
    @patch('langman.get_version', return_value='v1.0')
    @patch('langman.set_version')
    def test_get_from_cache(self, mock_set, mock_get, _, __, tmp_dirs):
        with patch.object(langman, 'CACHE_DIR', tmp_dirs['cache']):
            # Create cached artifact
            cache_dir = tmp_dirs['cache'] / 'python' / 'v1.0'
            cache_dir.mkdir(parents=True)
            artifact = cache_dir / 'libtree-sitter-python.dylib'
            artifact.write_bytes(b'test content')

            dest = tmp_dirs['dist']
            result = langman.get_from_cache('python', 'v1.0', dest)

            assert result is not None
            assert (dest / 'libtree-sitter-python.dylib').exists()

    @patch('langman.detect_extension', return_value='dylib')
    @patch('langman.set_version')
    def test_add_to_cache(self, mock_set, _, tmp_dirs):
        with patch.object(langman, 'CACHE_DIR', tmp_dirs['cache']):
            # Create artifact in dist
            artifact = tmp_dirs['dist'] / 'libtree-sitter-python.dylib'
            artifact.write_bytes(b'test content')

            langman.add_to_cache('python', 'v1.0', artifact)

            cached = tmp_dirs['cache'] / 'python' / 'v1.0' / 'libtree-sitter-python.dylib'
            assert cached.exists()


# --- Artifact Name Tests ---
class TestArtifactName:
    @patch('langman.detect_extension', return_value='dylib')
    def test_artifact_name_macos(self, _):
        assert langman.artifact_name('python') == 'libtree-sitter-python.dylib'

    @patch('langman.detect_extension', return_value='so')
    def test_artifact_name_linux(self, _):
        assert langman.artifact_name('python') == 'libtree-sitter-python.so'

    @patch('langman.detect_extension', return_value='dll')
    def test_artifact_name_windows(self, _):
        assert langman.artifact_name('python') == 'libtree-sitter-python.dll'


# --- Build Tests ---
class TestBuild:
    @patch('langman.detect_extension', return_value='dylib')
    @patch('langman.is_cached', return_value=False)
    @patch('langman.subprocess.run')
    @patch('langman.set_version')
    @patch('tempfile.mkdtemp')
    @patch('shutil.rmtree')
    def test_build_clones_repo(self, mock_rmtree, mock_mkdtemp, mock_set_version,
                               mock_run, mock_is_cached, mock_ext, tmp_dirs):
        with patch.object(langman, 'SCRIPT_DIR', tmp_dirs['dist'].parent):
            with patch.object(langman, 'DIST_DIR', tmp_dirs['dist']):
                mock_mkdtemp.return_value = str(tmp_dirs['cache'] / 'build')
                build_dir = tmp_dirs['cache'] / 'build'
                build_dir.mkdir(parents=True)

                # Create mock files that would be created during build
                lang_dir = build_dir / 'python'
                src_dir = lang_dir / 'src'
                src_dir.mkdir(parents=True)
                (src_dir / 'parser.c').touch()
                (src_dir / 'libtree-sitter-python.dylib').touch()

                mock_run.return_value = MagicMock(returncode=0, stdout='abc123\n')

                try:
                    langman.build_single('python')
                except Exception:
                    pass  # May fail due to mocking, but we verify git clone was called

                # Check that git clone was attempted
                clone_calls = [c for c in mock_run.call_args_list
                               if c[0][0][0] == 'git' and c[0][0][1] == 'clone']
                assert len(clone_calls) > 0

    @patch('langman.detect_extension', return_value='dylib')
    @patch('langman.is_cached', return_value=True)
    @patch('langman.get_from_cache')
    def test_build_uses_cache_when_versioned(self, mock_cache, mock_is_cached, mock_ext, tmp_dirs):
        with patch.object(langman, 'DIST_DIR', tmp_dirs['dist']):
            mock_cache.return_value = tmp_dirs['dist'] / 'libtree-sitter-python.dylib'

            langman.build_single('python', version='v1.0')

            mock_cache.assert_called_once_with('python', 'v1.0', tmp_dirs['dist'])


# --- CLI Tests ---
class TestCLI:
    def test_parse_args_build_single(self):
        args = langman.parse_args(['build', 'python'])
        assert args.command == 'build'
        assert args.language == 'python'
        assert args.version is None

    def test_parse_args_build_with_version(self):
        args = langman.parse_args(['build', '--version', 'v1.0', 'python'])
        assert args.command == 'build'
        assert args.language == 'python'
        assert args.version == 'v1.0'

    def test_parse_args_build_all(self):
        args = langman.parse_args(['build'])
        assert args.command == 'build'
        assert args.language is None

    def test_parse_args_install(self):
        args = langman.parse_args(['install', 'python'])
        assert args.command == 'install'
        assert args.language == 'python'

    def test_parse_args_version(self):
        args = langman.parse_args(['version', 'python'])
        assert args.command == 'version'
        assert args.language == 'python'


# --- Integration-style Tests (with more mocking) ---
class TestShowVersion:
    @patch('langman.detect_extension', return_value='dylib')
    @patch('langman.has_version', return_value=True)
    @patch('langman.get_version', return_value='v1.2.3')
    def test_show_version_installed(self, mock_get, mock_has, mock_ext, tmp_dirs):
        with patch.object(langman, 'DEFAULT_INSTALL_DIR', tmp_dirs['install']):
            artifact = tmp_dirs['install'] / 'libtree-sitter-python.dylib'
            artifact.touch()
            result = langman.show_version('python')
            assert result == 'v1.2.3'

    @patch('langman.detect_extension', return_value='dylib')
    def test_show_version_not_installed(self, mock_ext, tmp_dirs):
        with patch.object(langman, 'DEFAULT_INSTALL_DIR', tmp_dirs['install']):
            result = langman.show_version('python')
            assert result is None


# --- E2E Tests (real builds, slow, require network) ---
@pytest.fixture
def isolated_dirs(tmp_path, monkeypatch):
    """Create isolated cache/dist/install directories and patch langman globals."""
    dirs = {
        'cache': tmp_path / '.cache',
        'dist': tmp_path / 'dist',
        'install': tmp_path / 'install',
    }
    for d in dirs.values():
        d.mkdir(parents=True)

    # Patch langman module globals
    monkeypatch.setattr(langman, 'CACHE_DIR', dirs['cache'])
    monkeypatch.setattr(langman, 'DIST_DIR', dirs['dist'])
    monkeypatch.setattr(langman, 'DEFAULT_INSTALL_DIR', dirs['install'])
    monkeypatch.setenv('INSTALL_DIR', str(dirs['install']))

    return dirs


@pytest.mark.e2e
class TestE2E:
    """End-to-end tests that perform real builds (slow, require network)."""

    def test_build_head(self, isolated_dirs):
        """Build a grammar at HEAD."""
        # Build json (small grammar)
        result = langman.build_single('json')

        # Verify artifact exists in dist/
        art_name = langman.artifact_name('json')
        assert (isolated_dirs['dist'] / art_name).exists()
        assert result == isolated_dirs['dist'] / art_name

        # Verify version attribute contains HEAD@<sha>
        version = langman.get_version(result)
        assert version is not None
        assert version.startswith('HEAD@')
        assert len(version) > 6  # HEAD@ + at least 1 char of sha

    def test_build_versioned(self, isolated_dirs):
        """Build a grammar at a specific version."""
        # Build json at v0.24.8
        result = langman.build_single('json', version='v0.24.8')

        # Verify artifact exists
        art_name = langman.artifact_name('json')
        assert (isolated_dirs['dist'] / art_name).exists()

        # Verify version attribute is exactly v0.24.8
        version = langman.get_version(result)
        assert version == 'v0.24.8'

        # Verify cached in .cache/json/v0.24.8/
        cached_artifact = isolated_dirs['cache'] / 'json' / 'v0.24.8' / art_name
        assert cached_artifact.exists()
        assert langman.get_version(cached_artifact) == 'v0.24.8'

    def test_cache_hit(self, isolated_dirs, capsys):
        """Verify cache is used on second versioned build."""
        # First build
        langman.build_single('json', version='v0.24.8')
        capsys.readouterr()  # Clear captured output

        # Second build should use cache
        langman.build_single('json', version='v0.24.8')
        captured = capsys.readouterr()

        # Verify "Using cached" was printed
        assert 'Using cached' in captured.out

    def test_install(self, isolated_dirs):
        """Build and install a grammar."""
        # Install json at v0.24.8
        result = langman.install_single('json', version='v0.24.8')

        # Verify artifact exists in install dir
        art_name = langman.artifact_name('json')
        install_artifact = isolated_dirs['install'] / art_name
        assert install_artifact.exists()
        assert result == install_artifact

        # Verify version attribute is correct
        version = langman.get_version(install_artifact)
        assert version == 'v0.24.8'

    def test_show_version(self, isolated_dirs):
        """Show version of installed grammar."""
        # Install json
        langman.install_single('json', version='v0.24.8')

        # Call show_version()
        version = langman.show_version('json')

        # Verify returns correct version string
        assert version == 'v0.24.8'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
